from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from ai_agents.models import AIAgent, AIAgentLead
from ai_agents.services import sync_agents_for_user
from book.models import SavedBusiness
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from websitebuilder.services import create_starter_website


class CardbookMVPFlowTests(APITestCase):
    def authenticate(self, username, password):
        response = self.client.post(reverse("login"), {
            "username": username,
            "password": password,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return response

    def register_user(self, username, email, password="StrongPassword123!"):
        response = self.client.post(reverse("register"), {
            "username": username,
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": username.title(),
            "last_name": "Demo",
            "preferred_language": "es",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        return response.data["data"]["user"]

    def test_core_mvp_flow_from_registration_to_lead_and_book(self):
        owner = self.register_user("mvp_owner", "mvp-owner@example.com")
        self.authenticate("mvp_owner", "StrongPassword123!")

        mobile_config = self.client.get(reverse("mobile-config"))
        self.assertEqual(mobile_config.status_code, 200)
        self.assertIn("ai_agents", mobile_config.data["data"])

        company_response = self.client.post(reverse("company-list"), {
            "name": "MVP Technologies LLC",
            "phone_number": "9175550101",
            "email": "hello@mvp.test",
            "website": "https://mvp.test",
            "description": "Empresa demo para validar el flujo principal.",
            "category": "Tecnologia",
            "services": "Websites, tarjetas digitales, agentes IA",
            "city": "Paterson",
            "region": "NJ",
        }, format="json")
        self.assertEqual(company_response.status_code, 201)
        company_id = company_response.data["data"]["id"]
        company = Company.objects.get(pk=company_id)

        profile_response = self.client.post(reverse("card-list"), {
            "company": company_id,
            "job_title": "CEO",
            "phone_number": "9175550101",
            "email": "owner@mvp.test",
            "website": "https://mvp.test",
            "qr_shape": DigitalCard.QR_SHAPE_DIAMOND,
            "qr_dot_color": "#003875",
        }, format="json")
        self.assertEqual(profile_response.status_code, 201)
        profile_id = profile_response.data["data"]["id"]
        profile = DigitalCard.objects.get(pk=profile_id)
        self.assertTrue(profile.slug)
        self.assertIn("/c/", profile_response.data["data"]["public_url"])

        business_card_response = self.client.post(reverse("business-card-list"), {
            "profile": profile_id,
            "display_name": "MVP Owner Demo",
            "job_title": "CEO",
            "company_name": company.name,
            "phone_number": "9175550101",
            "email": "owner@mvp.test",
            "website": "https://mvp.test",
            "address": "Paterson, NJ",
            "tagline": "Conecta. Comparte. Crece.",
            "services": "Websites y tarjetas digitales",
            "include_qr": True,
        }, format="json")
        self.assertEqual(business_card_response.status_code, 201)
        business_card = BusinessCard.objects.get(pk=business_card_response.data["data"]["id"])
        self.assertIn("/c/presentacion/", business_card_response.data["data"]["public_url"])

        website = create_starter_website(company, publish=True)
        public_site_response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug}))
        self.assertEqual(public_site_response.status_code, 200)
        self.assertContains(public_site_response, company.name)

        owner_user = get_user_model().objects.get(pk=owner["id"])
        agent = sync_agents_for_user(owner_user)[1]
        agent.website = website
        agent.show_on_website = True
        agent.status = AIAgent.STATUS_ACTIVE
        agent.save(update_fields=["website", "show_on_website", "status", "updated_at"])

        public_ai_response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "message": "Que servicios ofrecen?",
        })
        self.assertEqual(public_ai_response.status_code, 200)
        self.assertTrue(public_ai_response.json()["success"])

        lead_response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "name": "Cliente MVP",
            "email": "cliente@mvp.test",
            "service_interest": "Website empresarial",
            "message": "Quiero una cotizacion.",
        })
        self.assertEqual(lead_response.status_code, 200)
        self.assertTrue(AIAgentLead.objects.filter(agent=agent, email="cliente@mvp.test").exists())

        self.client.credentials()
        self.register_user("mvp_visitor", "mvp-visitor@example.com")
        self.authenticate("mvp_visitor", "StrongPassword123!")
        book_response = self.client.post(reverse("book-list"), {
            "business_card": business_card.id,
            "notes": "Contacto guardado desde flujo MVP.",
        }, format="json")
        self.assertEqual(book_response.status_code, 201)
        self.assertTrue(SavedBusiness.objects.filter(company=company, business_card=business_card).exists())
