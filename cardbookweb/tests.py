import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from cardbookweb.qr import QRStyle, render_styled_qr_svg, style_from_object
from cardbookweb.test_utils import make_digital_card, make_user, make_white_card_job


class QRRendererTests(TestCase):
    def test_renderer_outputs_svg_with_expected_shape(self):
        svg = render_styled_qr_svg("https://incardbook.test/demo", QRStyle(shape="diamond"))

        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("viewBox", svg)
        self.assertIn("rotate(45", svg)

    def test_style_from_object_uses_safe_fallbacks(self):
        class UnsafeStyle:
            qr_dot_color = "blue"
            qr_marker_color = "#12345"
            qr_background_color = "#ffffff"
            qr_shape = "unknown"

        style = style_from_object(UnsafeStyle())

        self.assertEqual(style.dot_color, "#003875")
        self.assertEqual(style.marker_color, "#0057b8")
        self.assertEqual(style.background_color, "#ffffff")
        self.assertEqual(style.shape, "diamond")


class QREndpointTests(APITestCase):
    def test_public_card_qr_endpoint_returns_svg(self):
        user = make_user("qruser")
        card = make_digital_card(user=user)

        response = self.client.get(f"/c/{card.slug}/qr.svg", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)


class ObservabilityTests(APITestCase):
    def test_health_includes_request_id_and_response_header(self):
        response = self.client.get("/health/", HTTP_X_REQUEST_ID="trace-test-123")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["X-Request-ID"], "trace-test-123")
        self.assertEqual(response.json()["request_id"], "trace-test-123")

    @override_settings(CARDBOOK_REQUEST_LOGGING_ENABLED=True, CARDBOOK_SLOW_REQUEST_MS=0)
    def test_request_logging_includes_trace_fields(self):
        with self.assertLogs("cardbook.requests", level="INFO") as logs:
            response = self.client.get("/health/", HTTP_X_REQUEST_ID="trace-log-123")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        joined_logs = "\n".join(logs.output)
        self.assertIn("trace-log-123", joined_logs)
        self.assertIn("duration_ms", joined_logs)
        self.assertIn("/health/", joined_logs)

    @override_settings(CARDBOOK_REQUEST_LOGGING_ENABLED=True)
    def test_request_logging_records_client_errors(self):
        with self.assertLogs("cardbook.requests", level="WARNING") as logs:
            response = self.client.get("/missing-observability-page/", HTTP_X_REQUEST_ID="trace-404")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        joined_logs = "\n".join(logs.output)
        self.assertIn("trace-404", joined_logs)
        self.assertIn("404", joined_logs)

    @override_settings(
        DEBUG=False,
        EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
        DEFAULT_FROM_EMAIL="Cardbook <no-reply@incardbook.test>",
        USE_S3_MEDIA_STORAGE=True,
        AWS_STORAGE_BUCKET_NAME="cardbook-test-media",
        STRIPE_SECRET_KEY="sk_test_demo",
        STRIPE_WEBHOOK_SECRET="whsec_demo",
        CARDBOOK_ENABLE_REQUEST_ID_HEADERS=False,
    )
    def test_readiness_warns_when_request_id_headers_are_disabled_in_production(self):
        response = self.client.get("/health/ready/", secure=True)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn(
            "CARDBOOK_ENABLE_REQUEST_ID_HEADERS should remain enabled in production for traceability.",
            response.json()["production_config_issues"],
        )

    def test_white_card_job_qr_endpoint_returns_svg(self):
        job_card = make_white_card_job(user=make_user("qrworker"))

        response = self.client.get(f"/job/{job_card.username}/qr.svg", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)


class ProductionAuditCommandTests(TestCase):
    @override_settings(
        DEBUG=False,
        SECRET_KEY="prod-check-7f9a4d2c8b1e6h3k9m5p2r8t4w6y1z0q-cardbook-strong-secret",
        ALLOWED_HOSTS=["incardbook.test"],
        CSRF_TRUSTED_ORIGINS=["https://incardbook.test"],
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=31536000,
        X_FRAME_OPTIONS="DENY",
        USE_S3_MEDIA_STORAGE=True,
        AWS_STORAGE_BUCKET_NAME="cardbook-test-media",
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="smtp.incardbook.test",
        DEFAULT_FROM_EMAIL="Cardbook <no-reply@incardbook.test>",
        STRIPE_SECRET_KEY="sk_test_demo",
        STRIPE_WEBHOOK_SECRET="whsec_demo",
        CARDBOOK_ENABLE_REQUEST_ID_HEADERS=True,
    )
    def test_production_audit_outputs_success_json(self):
        output = StringIO()

        call_command("production_audit", "--json", stdout=output)

        payload = json.loads(output.getvalue())
        self.assertTrue(payload["success"])
        self.assertEqual(payload["errors"], 0)

    @override_settings(
        DEBUG=True,
        SECRET_KEY="django-insecure-demo",
        ALLOWED_HOSTS=["*"],
        CSRF_TRUSTED_ORIGINS=[],
        SECURE_SSL_REDIRECT=False,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        SECURE_HSTS_SECONDS=0,
        USE_S3_MEDIA_STORAGE=False,
        STRIPE_SECRET_KEY="",
        STRIPE_WEBHOOK_SECRET="",
    )
    def test_production_audit_strict_fails_on_errors(self):
        with self.assertRaises(CommandError):
            call_command("production_audit", "--strict", "--skip-db", stdout=StringIO())


class OpsSnapshotCommandTests(TestCase):
    def test_ops_snapshot_outputs_safe_json(self):
        output = StringIO()

        call_command("ops_snapshot", "--json", stdout=output)

        payload = json.loads(output.getvalue())
        self.assertTrue(payload["success"])
        self.assertEqual(payload["service"], "cardbook")
        self.assertIn("counts", payload)
        self.assertIn("accounts", payload["counts"])
        self.assertIn("companies", payload["counts"])
        serialized = json.dumps(payload)
        self.assertNotIn("password", serialized.lower())
        self.assertNotIn("secret", serialized.lower())
