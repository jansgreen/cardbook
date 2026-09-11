from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_published_website, make_user


class BusinessCardPrintTests(APITestCase):
    def test_print_view_can_render_double_qr_layout(self):
        owner = make_user("qrprintowner")
        company = make_company(owner=owner, name="La Costura de Dona Nancy")
        profile = make_digital_card(user=owner, company=company)
        business_card = make_business_card(
            profile=profile,
            display_name="Neyda Mendez",
            services="Ruedos y dobladillos\nAjuste de cinturas y caderas\nCambio de cierres\nReduccion o ampliacion de tallas",
        )
        self.client.force_login(owner)

        response = self.client.get(
            reverse("public-business-card-print", kwargs={"slug": business_card.slug}),
            {"layout": "qr_double"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QR doble")
        self.assertContains(response, "La Costura de Dona Nancy")
        self.assertContains(response, "Escanea mi tarjeta", count=2)
        self.assertContains(response, "Este codigo abre directamente la tarjeta digital publica.", count=2)
        self.assertContains(response, "Ruedos y dobladillos")
        self.assertContains(response, "Ajuste de cinturas y caderas")
        self.assertNotContains(response, "Compartir el perfil digital sin imprimir nuevas tarjetas.")


class BusinessCardDetailTests(APITestCase):
    @override_settings(CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="testserver")
    def test_detail_prefers_published_builder_website_url(self):
        owner = make_user("buildercardowner")
        company = make_company(owner=owner, name="Alta Costura Nancy")
        profile = make_digital_card(user=owner, company=company, website="https://old-profile.test")
        business_card = make_business_card(
            profile=profile,
            display_name="Neyda Mendez",
            website="https://old-card.test",
        )
        website = make_published_website(company=company)
        website.subdomain = "altacostura"
        website.save(update_fields=["subdomain", "updated_at"])

        response = self.client.get(reverse("public-business-card", kwargs={"slug": business_card.slug}), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://altacostura.testserver/")
        self.assertNotContains(response, "https://old-card.test")
