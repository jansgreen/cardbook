from rest_framework import status
from django.test import override_settings
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_published_website, make_user, make_white_card_job


class PublicMarketplaceTests(APITestCase):
    def setUp(self):
        owner = make_user("marketowner")
        company = make_company(owner=owner, name="BlueNova Technologies", category="Software", city="Paterson")
        profile = make_digital_card(user=owner, company=company, job_title="CEO")
        self.business_card = make_business_card(profile=profile, display_name="Luis Pena")
        self.white_card = make_white_card_job(user=make_user("worker"), specialty_name="Plomero", category="Servicios")
        self.website = make_published_website(company=company)

    def test_marketplace_api_returns_cards_jobs_and_websites(self):
        response = self.client.get("/api/v1/marketplace/?limit=2", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertGreaterEqual(data["summary"]["business_cards"], 1)
        self.assertGreaterEqual(data["summary"]["white_card_jobs"], 1)
        self.assertGreaterEqual(data["summary"]["websites"], 1)
        self.assertEqual(data["business_cards"][0]["type"], "business_card")
        self.assertIn("public_url", data["business_cards"][0])
        self.assertIn("qr_svg_url", data["business_cards"][0])
        self.assertEqual(data["white_card_jobs"][0]["type"], "white_card_job")
        self.assertEqual(data["websites"][0]["type"], "website")

    def test_marketplace_api_accepts_invalid_limit_without_crashing(self):
        response = self.client.get("/api/v1/marketplace/?limit=abc", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_public_companies_page_can_show_websites(self):
        response = self.client.get("/empresas/?type=websites", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Sitios publicados")
        self.assertContains(response, self.website.title)

    @override_settings(
        ALLOWED_HOSTS=["testserver", "incardbook.test", ".incardbook.test"],
        CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="incardbook.test",
    )
    def test_public_companies_page_links_to_website_subdomain(self):
        response = self.client.get("/empresas/?type=websites", HTTP_HOST="incardbook.test", secure=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, f"https://{self.website.subdomain}.incardbook.test/")
