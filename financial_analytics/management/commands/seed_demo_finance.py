from decimal import Decimal

from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from billing.models import Invoice, Payment
from companies.models import Company
from financial_analytics.models import ReferralClick
from financial_analytics.services import create_commission_from_payment
from referrals.models import AgentProfile
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = "Create demo financial data for Cardbook finance dashboard."

    def handle(self, *args, **options):
        User = get_user_model()
        finance_admin, _ = User.objects.update_or_create(
            username="finance_admin",
            defaults={
                "email": "finance.admin@demo.cardbook.test",
                "first_name": "Finance",
                "last_name": "Admin",
                "is_staff": True,
                "is_active": True,
            },
        )
        finance_admin.set_password("CardbookDemo123!")
        finance_admin.save(update_fields=["password", "updated_at"])
        finance_admin.user_permissions.set(Permission.objects.filter(codename__in=[
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
        ]))
        agent_user = User.objects.filter(username__icontains="agent").first() or User.objects.first()
        agent = AgentProfile.objects.filter(user=agent_user).first() if agent_user else None
        if agent_user and not agent:
            agent = AgentProfile.objects.create(user=agent_user)
        companies = list(Company.objects.filter(is_active=True)[:5])
        if not agent or not companies:
            self.stdout.write(self.style.WARNING("Create users and companies before running this command."))
            return

        plans = [
            ("Basic", Decimal("19.00"), Decimal("0.95"), Decimal("15.00")),
            ("Pro", Decimal("29.00"), Decimal("1.45"), Decimal("20.00")),
            ("Premium", Decimal("49.00"), Decimal("2.45"), Decimal("25.00")),
        ]
        created_payments = 0
        for index, company in enumerate(companies, start=1):
            plan, amount, stripe_fee, commission_percent = plans[index % len(plans)]
            subscription, _ = Subscription.objects.update_or_create(
                company=company,
                stripe_subscription_id=f"sub_demo_{company.id}",
                defaults={
                    "stripe_customer_id": f"cus_demo_{company.id}",
                    "plan": plan,
                    "unit_amount": amount,
                    "currency": "USD",
                    "status": Subscription.STATUS_ACTIVE,
                    "billing_interval": Subscription.INTERVAL_MONTHLY,
                    "current_period_start": timezone.now(),
                    "current_period_end": timezone.now() + timezone.timedelta(days=30),
                },
            )
            invoice, _ = Invoice.objects.update_or_create(
                stripe_invoice_id=f"in_demo_{company.id}",
                defaults={
                    "company": company,
                    "subscription": subscription,
                    "invoice_number": f"CB-{company.id:04d}",
                    "subtotal": amount,
                    "total": amount,
                    "amount_paid": amount,
                    "currency": "USD",
                    "status": Invoice.STATUS_PAID,
                    "paid_at": timezone.now(),
                },
            )
            payment, created = Payment.objects.update_or_create(
                stripe_payment_intent_id=f"pi_demo_{company.id}",
                defaults={
                    "company": company,
                    "subscription": subscription,
                    "invoice": invoice,
                    "stripe_invoice_id": invoice.stripe_invoice_id,
                    "amount": amount,
                    "currency": "USD",
                    "status": Payment.STATUS_SUCCEEDED,
                    "payment_method": "card",
                    "stripe_fee": stripe_fee,
                    "net_amount": amount - stripe_fee,
                    "paid_at": timezone.now(),
                },
            )
            ReferralClick.objects.get_or_create(agent=agent, referral_code=f"AGENT-{agent.id}", landing_page="/register/")
            create_commission_from_payment(payment, agent, commission_percent)
            if created:
                created_payments += 1

        self.stdout.write(self.style.SUCCESS(f"Demo financial data ready. New payments: {created_payments}"))
        self.stdout.write("Finance admin: finance_admin / CardbookDemo123!")
