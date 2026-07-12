from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework.test import APIClient

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import PERM_CREATE_CARDBOOK_BUSINESS_CARDS, ensure_default_permissions
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from financial_analytics.models import AuditLog
from referrals.models import AgentCardSale, AgentProfile, Commission, ReferralNotification
from referrals.services import record_agent_card_sale, unread_notification_count


class AgentCardSaleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", email="owner@example.com", password="pass12345")
        self.agent_user = User.objects.create_user(username="agent", email="agent@example.com", password="pass12345")
        self.regular_user = User.objects.create_user(username="regular", email="regular@example.com", password="pass12345")
        self.finance_admin = User.objects.create_user(username="finance", email="finance@example.com", password="pass12345", is_staff=True)
        self.company = Company.objects.create(owner=self.owner, name="Cardbook", is_active=True)
        ensure_default_permissions()
        self.agent_role = AccessRole.objects.get(name="Agente Cardbook")
        self.agent_role.default_commission_percent = Decimal("15.00")
        self.agent_role.save(update_fields=["default_commission_percent"])

    def test_agent_profile_sale_creates_agent_profile_sale_and_commission(self):
        UserAccessGrant.objects.create(
            user=self.agent_user,
            company=self.company,
            role=self.agent_role,
            commission_percent=Decimal("12.50"),
            is_active=True,
        )
        profile = DigitalCard.objects.create(
            company=self.company,
            user=self.agent_user,
            job_title="Agente",
            email="agent@example.com",
        )

        sale = record_agent_card_sale(user=self.agent_user, digital_card=profile)

        self.assertIsNotNone(sale)
        self.assertEqual(sale.sale_type, AgentCardSale.SALE_TYPE_PROFILE)
        self.assertEqual(sale.commission_percentage, Decimal("12.50"))
        self.assertEqual(sale.status, AgentCardSale.STATUS_COMMISSIONED)
        self.assertTrue(AgentProfile.objects.filter(user=self.agent_user).exists())
        self.assertTrue(Commission.objects.filter(agent=sale.agent, company=self.company, status=Commission.STATUS_PENDING).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.ACTION_AGENT_CARD_SALE, actor=self.agent_user).exists())
        self.assertTrue(ReferralNotification.objects.filter(recipient=self.agent_user, event_type=ReferralNotification.TYPE_AGENT_SALE).exists())
        self.assertTrue(ReferralNotification.objects.filter(recipient=self.finance_admin, event_type=ReferralNotification.TYPE_FINANCE_ALERT).exists())

    def test_agent_business_card_sale_is_not_duplicated(self):
        UserAccessGrant.objects.create(
            user=self.agent_user,
            company=self.company,
            role=self.agent_role,
            commission_percent=Decimal("10.00"),
            is_active=True,
        )
        profile = DigitalCard.objects.create(company=self.company, user=self.agent_user, job_title="Agente")
        business_card = BusinessCard.objects.create(
            profile=profile,
            display_name="Agente Demo",
            company_name=self.company.name,
            email="agent@example.com",
        )

        first_sale = record_agent_card_sale(user=self.agent_user, business_card=business_card)
        second_sale = record_agent_card_sale(user=self.agent_user, business_card=business_card)

        self.assertEqual(first_sale.id, second_sale.id)
        self.assertEqual(AgentCardSale.objects.filter(business_card=business_card).count(), 1)
        self.assertEqual(Commission.objects.filter(card_sale__business_card=business_card).count(), 1)

    def test_regular_user_does_not_create_agent_sale(self):
        profile = DigitalCard.objects.create(company=self.company, user=self.regular_user, job_title="Staff")

        sale = record_agent_card_sale(user=self.regular_user, digital_card=profile)

        self.assertIsNone(sale)
        self.assertFalse(AgentCardSale.objects.exists())
        self.assertFalse(Commission.objects.exists())

    def test_agent_role_without_business_card_permission_does_not_create_sale(self):
        role = AccessRole.objects.create(name="Agente sin tarjeta", is_agent_role=True, default_commission_percent=Decimal("20.00"))
        UserAccessGrant.objects.create(user=self.agent_user, company=self.company, role=role, is_active=True)
        profile = DigitalCard.objects.create(company=self.company, user=self.agent_user, job_title="Agente")

        sale = record_agent_card_sale(user=self.agent_user, digital_card=profile)

        self.assertIsNone(sale)
        self.assertFalse(AgentCardSale.objects.exists())
        self.assertFalse(AgentProfile.objects.filter(user=self.agent_user).exists())
        self.assertFalse(Commission.objects.exists())

    def test_notification_inbox_and_mark_read(self):
        notification = ReferralNotification.objects.create(
            recipient=self.agent_user,
            event_type=ReferralNotification.TYPE_COMMISSION,
            title="Comision generada",
            message="Tienes una comision pendiente.",
        )
        client = Client()
        client.force_login(self.agent_user)

        response = client.get("/dashboard/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Comision generada")
        self.assertEqual(unread_notification_count(self.agent_user), 1)

        response = client.post("/dashboard/notifications/", {"notification_id": notification.id})

        self.assertEqual(response.status_code, 302)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
        self.assertEqual(unread_notification_count(self.agent_user), 0)

    def test_notification_api_lists_and_marks_read(self):
        notification = ReferralNotification.objects.create(
            recipient=self.agent_user,
            event_type=ReferralNotification.TYPE_PAID,
            title="Comision pagada",
        )
        client = APIClient()
        client.force_authenticate(self.agent_user)

        response = client.get("/api/v1/referrals/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["unread_count"], 1)
        self.assertEqual(response.json()["data"]["results"][0]["id"], notification.id)

        response = client.post(f"/api/v1/referrals/notifications/{notification.id}/mark-read/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["unread_count"], 0)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
