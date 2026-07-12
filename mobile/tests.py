from rest_framework import status
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_published_website, make_user, make_white_card_job


class MobileBFFTests(APITestCase):
    def setUp(self):
        self.user = make_user("mobileuser")
        self.company = make_company(owner=self.user, name="Mobile Co")
        self.profile = make_digital_card(user=self.user, company=self.company)
        self.business_card = make_business_card(profile=self.profile)
        self.white_card = make_white_card_job(user=make_user("mobileworker"))
        self.website = make_published_website(company=self.company)
        self.client.force_authenticate(self.user)

    def test_mobile_bootstrap_returns_navigation_and_capabilities(self):
        response = self.client.get("/api/v1/mobile/bootstrap/", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertIn("navigation", data)
        self.assertIn("capabilities", data)
        self.assertTrue(data["capabilities"]["can_create_digital_card"])
        self.assertTrue(data["capabilities"]["can_create_business_card"])

    def test_mobile_screen_endpoints_return_success(self):
        for path in [
            "/api/v1/mobile/dashboard/",
            "/api/v1/mobile/companies/",
            "/api/v1/mobile/cards/",
            "/api/v1/mobile/book/",
            "/api/v1/mobile/jobs/",
            "/api/v1/mobile/websites/",
            "/api/v1/mobile/actions/",
        ]:
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST="127.0.0.1:8000")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data["success"])

    def test_mobile_cards_include_public_and_qr_urls(self):
        response = self.client.get("/api/v1/mobile/cards/", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        digital_card = response.data["data"]["digital_cards"][0]
        business_card = response.data["data"]["business_cards"][0]
        self.assertIn("public_url", digital_card)
        self.assertIn("qr_svg_url", digital_card)
        self.assertIn("public_url", business_card)
        self.assertIn("qr_svg_url", business_card)
