from decimal import Decimal
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import Client
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from billing.models import Invoice, Payment, Refund, StripeEvent
from cardbookweb.test_utils import make_company, make_user
from financial_analytics.models import AuditLog, CommissionPayment, ReferralClick
from financial_analytics.permissions import can_view_agent_finance
from financial_analytics.services import calculate_arr, calculate_mrr, calculate_net_revenue, create_commission_from_payment
from referrals.models import AgentProfile, Commission
from subscriptions.models import Subscription


class FinancialAnalyticsTests(APITestCase):
    def setUp(self):
        self.admin = make_user("finance_admin", is_staff=True)
        permissions = Permission.objects.filter(
            codename__in=[
                "can_view_financial_dashboard",
                "can_view_revenue",
                "can_view_subscriptions",
                "can_view_companies_billing",
                "can_view_referrals",
                "can_view_commissions",
                "can_approve_commissions",
                "can_mark_commissions_paid",
                "can_view_payments",
                "can_process_refunds",
                "can_export_financial_reports",
                "can_access_stripe_dashboard",
            ]
        )
        self.admin.user_permissions.set(permissions)
        self.admin.is_superuser = True
        self.admin.save(update_fields=["is_superuser"])
        self.company = make_company(owner=self.admin, name="Finance Test Co")
        self.subscription = Subscription.objects.create(
            company=self.company,
            stripe_subscription_id="sub_test_001",
            plan="Pro",
            unit_amount=Decimal("29.00"),
            status=Subscription.STATUS_ACTIVE,
            billing_interval=Subscription.INTERVAL_MONTHLY,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.payment = Payment.objects.create(
            company=self.company,
            subscription=self.subscription,
            stripe_payment_intent_id="pi_test_001",
            amount=Decimal("29.00"),
            stripe_fee=Decimal("1.20"),
            net_amount=Decimal("27.80"),
            status=Payment.STATUS_SUCCEEDED,
            paid_at=timezone.now(),
        )

    def test_financial_formulas(self):
        self.assertEqual(calculate_mrr(), Decimal("29.00"))
        self.assertEqual(calculate_arr(), Decimal("348.00"))
        self.assertEqual(calculate_net_revenue(), Decimal("27.80"))

    def test_overview_requires_financial_permission(self):
        user = make_user("regular_user")
        self.client.force_authenticate(user)
        forbidden = self.client.get(reverse("api-finance-overview"))
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("api-finance-overview"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["metrics"]["mrr"], Decimal("29.00"))

    def test_commission_approval_and_paid_flow(self):
        agent_user = make_user("agent_finance")
        agent = AgentProfile.objects.create(user=agent_user)
        ReferralClick.objects.create(agent=agent, referral_code="AGENT100")
        commission = create_commission_from_payment(self.payment, agent, Decimal("20.00"))
        self.assertEqual(commission.commission_amount, Decimal("5.80"))

        self.client.force_authenticate(self.admin)
        approve = self.client.post(reverse("api-finance-commission-approve", args=[commission.id]))
        self.assertEqual(approve.status_code, status.HTTP_200_OK)
        self.assertEqual(approve.data["data"]["status"], Commission.STATUS_APPROVED)

        mark_paid = self.client.post(reverse("api-finance-commission-paid", args=[commission.id]))
        self.assertEqual(mark_paid.status_code, status.HTTP_200_OK)
        self.assertEqual(mark_paid.data["data"]["status"], Commission.STATUS_PAID)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_COMMISSION_APPROVED, actor=self.admin).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_COMMISSION_PAID, actor=self.admin).exists())

    def test_finance_commissions_page_can_approve_and_mark_paid(self):
        agent_user = make_user("agent_page")
        agent = AgentProfile.objects.create(user=agent_user)
        commission = create_commission_from_payment(self.payment, agent, Decimal("20.00"))

        self.client.force_authenticate(self.admin)
        approve = self.client.post(
            reverse("finance-commissions"),
            {"action": "approve_commission", "commission_id": commission.id},
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(approve.status_code, status.HTTP_302_FOUND)
        commission.refresh_from_db()
        self.assertEqual(commission.status, Commission.STATUS_APPROVED)
        self.assertEqual(commission.approved_by, self.admin)

        mark_paid = self.client.post(
            reverse("finance-commissions"),
            {"action": "mark_commission_paid", "commission_id": commission.id},
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(mark_paid.status_code, status.HTTP_302_FOUND)
        commission.refresh_from_db()
        self.assertEqual(commission.status, Commission.STATUS_PAID)
        self.assertEqual(commission.paid_by, self.admin)

    def test_finance_commissions_page_blocks_action_without_permission(self):
        view_only = make_user("commission_view_only")
        view_only.user_permissions.add(Permission.objects.get(codename="can_view_commissions"))
        agent = AgentProfile.objects.create(user=make_user("agent_denied"))
        commission = create_commission_from_payment(self.payment, agent, Decimal("20.00"))

        self.client.force_authenticate(view_only)
        response = self.client.post(
            reverse("finance-commissions"),
            {"action": "approve_commission", "commission_id": commission.id},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        commission.refresh_from_db()
        self.assertEqual(commission.status, Commission.STATUS_PENDING)

    def test_finance_commissions_page_filters_by_status(self):
        agent = AgentProfile.objects.create(user=make_user("agent_filter"))
        pending = create_commission_from_payment(self.payment, agent, Decimal("20.00"))
        approved = Commission.objects.create(
            agent=agent,
            company=self.company,
            plan_name="Manual approved",
            payment_amount=Decimal("10.00"),
            commission_percentage=Decimal("10.00"),
            commission_amount=Decimal("1.00"),
            status=Commission.STATUS_APPROVED,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("finance-commissions"),
            {"status": Commission.STATUS_APPROVED},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, approved.plan_name)
        self.assertNotContains(response, pending.plan_name)

    def test_finance_report_commissions_csv_uses_filters(self):
        agent = AgentProfile.objects.create(user=make_user("agent_csv"))
        pending = create_commission_from_payment(self.payment, agent, Decimal("20.00"))
        Commission.objects.create(
            agent=agent,
            company=self.company,
            plan_name="Paid commission",
            payment_amount=Decimal("20.00"),
            commission_percentage=Decimal("10.00"),
            commission_amount=Decimal("2.00"),
            status=Commission.STATUS_PAID,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("finance-report-csv", args=["commissions"]),
            {"status": Commission.STATUS_PENDING},
            HTTP_HOST="127.0.0.1",
        )
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(pending.plan_name, content)
        self.assertNotIn("Paid commission", content)

    def test_finance_report_csv_requires_reports_permission(self):
        view_only = make_user("report_view_only")
        view_only.user_permissions.add(Permission.objects.get(codename="can_view_commissions"))

        self.client.force_authenticate(view_only)
        response = self.client.get(reverse("finance-report-csv", args=["commissions"]), HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finance_audit_page_renders_events(self):
        AuditLog.objects.create(
            actor=self.admin,
            action=AuditLog.ACTION_REPORT_EXPORTED,
            title="Reporte CSV exportado",
            message="Prueba de auditoria",
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("finance-audit"), HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Reporte CSV exportado")
        self.assertContains(response, "report.exported")
        self.assertNotContains(response, "Â·")

    def test_agent_finance_permission_matches_agent_user(self):
        agent_user = make_user("agent_permission")
        agent = AgentProfile.objects.create(user=agent_user)
        other_user = make_user("not_agent_permission")

        self.assertTrue(can_view_agent_finance(agent_user, agent))
        self.assertFalse(can_view_agent_finance(other_user, agent))

    def test_report_export_creates_audit_log(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("finance-report-csv", args=["agents"]), HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_REPORT_EXPORTED, actor=self.admin, target_id="agents").exists())

    def test_report_exports_include_production_finance_csvs(self):
        self.client.force_authenticate(self.admin)
        for report_key in ["refunds", "subscriptions", "companies"]:
            response = self.client.get(reverse("finance-report-csv", args=[report_key]), HTTP_HOST="127.0.0.1")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "text/csv")

    def test_refund_requires_stripe_or_explicit_manual_mode(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(reverse("api-finance-payment-refund", args=[self.payment.id]), {"amount": "5.00"})

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(Refund.objects.exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_REFUND_FAILED, actor=self.admin).exists())

    @override_settings(STRIPE_ALLOW_MANUAL_REFUNDS=True)
    def test_manual_refund_creates_refund_and_audit_log(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("api-finance-payment-refund", args=[self.payment.id]),
            {"amount": "5.00", "reason": "Customer request", "manual": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        refund = Refund.objects.get()
        self.assertEqual(refund.amount, Decimal("5.00"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PARTIALLY_REFUNDED)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_REFUND_CREATED, actor=self.admin).exists())

    def test_agent_payout_creates_commission_payment_and_marks_commissions_paid(self):
        agent = AgentProfile.objects.create(user=make_user("agent_payout"))
        first = Commission.objects.create(
            agent=agent,
            company=self.company,
            plan_name="Approved one",
            payment_amount=Decimal("40.00"),
            commission_percentage=Decimal("10.00"),
            commission_amount=Decimal("4.00"),
            status=Commission.STATUS_APPROVED,
        )
        second = Commission.objects.create(
            agent=agent,
            company=self.company,
            plan_name="Approved two",
            payment_amount=Decimal("60.00"),
            commission_percentage=Decimal("10.00"),
            commission_amount=Decimal("6.00"),
            status=Commission.STATUS_APPROVED,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("api-finance-agent-payout-create", args=[agent.id]),
            {
                "commission_ids": [first.id, second.id],
                "payment_method": "zelle",
                "transaction_reference": "zelle-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payout = CommissionPayment.objects.get()
        self.assertEqual(payout.total_amount, Decimal("10.00"))
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, Commission.STATUS_PAID)
        self.assertEqual(second.status, Commission.STATUS_PAID)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_AGENT_PAYOUT_CREATED, actor=self.admin).exists())

    @override_settings(STRIPE_SECRET_KEY="sk_test_123")
    def test_customer_portal_returns_stripe_url(self):
        self.subscription.stripe_customer_id = "cus_test_001"
        self.subscription.save(update_fields=["stripe_customer_id"])
        self.client.force_authenticate(self.admin)

        with patch("financial_analytics.views.create_customer_portal_session") as create_session:
            create_session.return_value = SimpleNamespace(id="bps_test_001", url="https://billing.stripe.com/session/test")
            response = self.client.post(reverse("api-billing-customer-portal"), {"company_id": self.company.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["url"], "https://billing.stripe.com/session/test")

    def test_finance_dashboard_pages_render(self):
        self.client.force_authenticate(self.admin)
        paths = [
            "/dashboard/finance/",
            "/dashboard/finance/revenue/",
            "/dashboard/finance/subscriptions/",
            "/dashboard/finance/companies/",
            "/dashboard/finance/referrals/",
            "/dashboard/finance/commissions/",
            "/dashboard/finance/payments/",
            "/dashboard/finance/refunds/",
            "/dashboard/finance/reports/",
            "/dashboard/finance/audit/",
        ]
        for path in paths:
            response = self.client.get(path, HTTP_HOST="127.0.0.1")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_finance_dashboard_accepts_browser_session_login(self):
        browser = Client()
        browser.force_login(self.admin)

        response = browser.get("/dashboard/finance/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "<title>Finanzas | Cardbook</title>", html=True)
        self.assertContains(response, "Panel de gestion")
        self.assertContains(response, "finance-tabs")
        self.assertNotContains(response, "Cardbook API is running")

    @override_settings(STRIPE_ALLOW_MANUAL_REFUNDS=True, STRIPE_SECRET_KEY="")
    def test_finance_payments_page_can_process_manual_refund(self):
        browser = Client()
        browser.force_login(self.admin)

        page = browser.get(reverse("finance-payments"), HTTP_HOST="127.0.0.1")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        self.assertContains(page, "Modo manual activo")
        self.assertContains(page, "Reembolsar")

        response = browser.post(
            reverse("finance-payments"),
            {
                "action": "refund_payment",
                "payment_id": self.payment.id,
                "amount": "5.00",
                "reason": "Solicitud del cliente",
                "manual": "1",
            },
            HTTP_HOST="127.0.0.1",
        )
        self.assertRedirects(response, reverse("finance-payments"), fetch_redirect_response=False)

        refund = Refund.objects.get(payment=self.payment)
        self.assertEqual(refund.amount, Decimal("5.00"))
        self.assertEqual(refund.status, Refund.STATUS_PENDING)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PARTIALLY_REFUNDED)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_REFUND_CREATED, actor=self.admin).exists())

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_stripe_webhook_validates_signature_and_is_idempotent(self):
        payload = json.dumps({"id": "evt_test_001", "type": "payment_intent.succeeded"}).encode("utf-8")
        timestamp = str(int(time.time()))
        signed_payload = timestamp.encode("utf-8") + b"." + payload
        signature = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()

        response = self.client.post(
            reverse("api-stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["processed"])

        duplicate = self.client.post(
            reverse("api-stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_200_OK)
        self.assertFalse(duplicate.data["data"]["processed"])

        invalid = self.client.post(
            reverse("api-stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1=bad",
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_stripe_subscription_webhook_syncs_subscription(self):
        payload = {
            "id": "evt_sub_sync",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_sync_001",
                    "customer": "cus_sync_001",
                    "status": "active",
                    "currency": "usd",
                    "current_period_start": int(time.time()),
                    "current_period_end": int(time.time()) + 2592000,
                    "cancel_at_period_end": False,
                    "metadata": {"company_id": str(self.company.id), "plan": "Business"},
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "unit_amount": 4900,
                                    "nickname": "Business",
                                    "recurring": {"interval": "month"},
                                }
                            }
                        ]
                    },
                }
            },
        }

        response = self.client.post(reverse("api-stripe-webhook"), data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["synced"])
        subscription = Subscription.objects.get(stripe_subscription_id="sub_sync_001")
        self.assertEqual(subscription.company, self.company)
        self.assertEqual(subscription.plan, "Business")
        self.assertEqual(subscription.unit_amount, Decimal("49.00"))

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_stripe_invoice_payment_and_refund_webhooks_sync_finance_records(self):
        self.subscription.stripe_customer_id = "cus_sync_002"
        self.subscription.save(update_fields=["stripe_customer_id"])
        invoice_payload = {
            "id": "evt_invoice_sync",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_sync_001",
                    "number": "INV-001",
                    "customer": "cus_sync_002",
                    "subscription": self.subscription.stripe_subscription_id,
                    "subtotal": 2900,
                    "tax": 0,
                    "total": 2900,
                    "amount_paid": 2900,
                    "amount_due": 0,
                    "currency": "usd",
                    "status": "paid",
                    "hosted_invoice_url": "https://pay.stripe.com/invoice/test",
                    "invoice_pdf": "https://pay.stripe.com/invoice/test.pdf",
                    "status_transitions": {"paid_at": int(time.time())},
                }
            },
        }
        payment_payload = {
            "id": "evt_payment_sync",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_sync_001",
                    "invoice": "in_sync_001",
                    "customer": "cus_sync_002",
                    "amount": 2900,
                    "amount_received": 2900,
                    "currency": "usd",
                    "status": "succeeded",
                    "created": int(time.time()),
                    "payment_method_types": ["card"],
                }
            },
        }
        refund_payload = {
            "id": "evt_refund_sync",
            "type": "refund.updated",
            "data": {
                "object": {
                    "id": "re_sync_001",
                    "payment_intent": "pi_sync_001",
                    "amount": 500,
                    "currency": "usd",
                    "status": "succeeded",
                    "reason": "requested_by_customer",
                }
            },
        }

        for payload in [invoice_payload, payment_payload, refund_payload]:
            response = self.client.post(reverse("api-stripe-webhook"), data=json.dumps(payload), content_type="application/json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data["data"]["processed"])
            self.assertTrue(response.data["data"]["synced"])

        invoice = Invoice.objects.get(stripe_invoice_id="in_sync_001")
        payment = Payment.objects.get(stripe_payment_intent_id="pi_sync_001")
        refund = Refund.objects.get(stripe_refund_id="re_sync_001")
        self.assertEqual(invoice.amount_paid, Decimal("29.00"))
        self.assertEqual(payment.invoice, invoice)
        self.assertEqual(payment.status, Payment.STATUS_PARTIALLY_REFUNDED)
        self.assertEqual(refund.amount, Decimal("5.00"))
        self.assertEqual(StripeEvent.objects.filter(event_id__in=["evt_invoice_sync", "evt_payment_sync", "evt_refund_sync"]).count(), 3)
