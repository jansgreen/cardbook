from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import SupportTicket


class SupportTicketAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="supportuser",
            email="support@example.com",
            password="pass12345",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_user_can_create_and_list_support_ticket(self):
        response = self.client.post(
            "/api/v1/support/tickets/",
            {
                "category": "mobile",
                "priority": "normal",
                "subject": "Problema en app movil",
                "message": "La aplicacion no muestra mis tarjetas correctamente.",
                "technical_context": {"source": "test"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(SupportTicket.objects.filter(user=self.user).count(), 1)

        response = self.client.get("/api/v1/support/tickets/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["subject"], "Problema en app movil")
