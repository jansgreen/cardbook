from django.urls import reverse
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_user


class BusinessCardPrintTests(APITestCase):
    def test_print_view_can_render_double_qr_layout(self):
        owner = make_user("qrprintowner")
        company = make_company(owner=owner, name="La Costura de Dona Nancy")
        profile = make_digital_card(user=owner, company=company)
        business_card = make_business_card(profile=profile, display_name="Neyda Mendez")
        self.client.force_login(owner)

        response = self.client.get(
            reverse("public-business-card-print", kwargs={"slug": business_card.slug}),
            {"layout": "qr_double"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QR doble")
        self.assertContains(response, "Escanea mi tarjeta", count=2)
        self.assertContains(response, "Este codigo abre directamente la tarjeta digital publica.", count=2)
