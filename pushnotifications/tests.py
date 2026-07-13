from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import PushDeliveryLog, PushDevice


class PushNotificationAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pushuser",
            email="push@example.com",
            password="pass12345",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_register_and_disable_push_device(self):
        token = "fcm-token-" + ("x" * 64)
        response = self.client.post(
            "/api/v1/push/devices/",
            {
                "token": token,
                "platform": "android",
                "device_id": "emulator-5554",
                "app_version": "0.1.2+3",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PushDevice.objects.filter(user=self.user, enabled=True).count(), 1)

        response = self.client.post("/api/v1/push/devices/disable/", {"token": token}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(PushDevice.objects.get(token=token).enabled)

    def test_push_test_is_skipped_when_fcm_is_not_configured(self):
        PushDevice.objects.create(user=self.user, token="fcm-token-" + ("y" * 64))

        response = self.client.post("/api/v1/push/test/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PushDeliveryLog.objects.filter(user=self.user).count(), 1)
        self.assertEqual(PushDeliveryLog.objects.get(user=self.user).status, PushDeliveryLog.STATUS_SKIPPED)
