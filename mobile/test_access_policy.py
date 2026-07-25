from rest_framework import status
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_company, make_digital_card, make_user


class MobileAccessPolicyTests(APITestCase):
    def get_bootstrap_data(self, user):
        self.client.force_authenticate(user)
        response = self.client.get("/api/v1/mobile/bootstrap/", HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["data"]

    def test_job_user_receives_job_menu_and_capabilities(self):
        user = make_user("mobilejob", registration_intent="job")

        data = self.get_bootstrap_data(user)
        menu_keys = {item["key"] for item in data["menu"]}

        self.assertEqual(data["registration_intent"], "job")
        self.assertEqual(data["account_type"], "job")
        self.assertEqual(menu_keys, {"companies", "white_card_job", "notifications", "book"})
        self.assertFalse(data["capabilities"]["can_create_company"])
        self.assertTrue(data["capabilities"]["can_create_white_card_job"])
        self.assertTrue(data["capabilities"]["can_use_book"])
        self.assertNotIn("cards", data["allowed_sections"])
        self.assertNotIn("finance", data["allowed_sections"])

    def test_company_user_receives_company_menu_and_capabilities(self):
        user = make_user("mobilecompany", registration_intent="company")
        company = make_company(owner=user)
        make_digital_card(user=user, company=company)

        data = self.get_bootstrap_data(user)
        menu_keys = {item["key"] for item in data["menu"]}

        self.assertEqual(data["registration_intent"], "company")
        self.assertEqual(data["account_type"], "company")
        self.assertIn("cards", menu_keys)
        self.assertIn("business_cards", menu_keys)
        self.assertIn("website", menu_keys)
        self.assertNotIn("white_card_job", menu_keys)
        self.assertNotIn("referrals", menu_keys)
        self.assertTrue(data["capabilities"]["can_create_company"])
        self.assertTrue(data["capabilities"]["can_create_digital_card"])
        self.assertFalse(data["capabilities"]["can_view_finance"])

    def test_agent_user_receives_agent_menu_without_finance_or_access(self):
        user = make_user("mobileagent", registration_intent="agent")

        data = self.get_bootstrap_data(user)
        menu_keys = {item["key"] for item in data["menu"]}

        self.assertEqual(data["account_type"], "agent")
        self.assertIn("referrals", menu_keys)
        self.assertIn("white_card_job", menu_keys)
        self.assertIn("cards", menu_keys)
        self.assertNotIn("finance", menu_keys)
        self.assertNotIn("access", menu_keys)
        self.assertTrue(data["capabilities"]["can_view_referrals"])
        self.assertFalse(data["capabilities"]["can_view_finance"])
        self.assertFalse(data["capabilities"]["can_manage_access"])

    def test_superuser_receives_admin_only_mobile_permissions(self):
        user = make_user("mobilesuper", is_superuser=True, is_staff=True)

        data = self.get_bootstrap_data(user)
        menu_keys = {item["key"] for item in data["menu"]}

        self.assertEqual(data["account_type"], "superuser")
        self.assertIn("finance", menu_keys)
        self.assertIn("access", menu_keys)
        self.assertTrue(data["capabilities"]["can_view_finance"])
        self.assertTrue(data["capabilities"]["can_manage_access"])

    def test_mobile_dashboard_includes_same_access_payload(self):
        user = make_user("mobiledashjob", registration_intent="job")
        self.client.force_authenticate(user)

        response = self.client.get("/api/v1/mobile/dashboard/", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["account_type"], "job")
        self.assertEqual({item["key"] for item in data["navigation"]}, {"companies", "white_card_job", "notifications", "book"})
