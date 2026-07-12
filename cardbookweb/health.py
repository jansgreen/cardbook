from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views import View


class HealthView(View):
    check_database = False
    check_production_config = False

    def get(self, request, *args, **kwargs):
        payload = {
            "success": True,
            "service": "cardbook",
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.DEPLOY_ENV,
            "commit": settings.RELEASE_COMMIT[:12] if settings.RELEASE_COMMIT else "unknown",
            "debug": settings.DEBUG,
            "request_id": getattr(request, "cardbook_request_id", ""),
            "checked_at": timezone.now().isoformat(),
        }

        status_code = 200
        if self.check_database:
            try:
                connection.ensure_connection()
                payload["database"] = "ok"
            except Exception as exc:
                payload["success"] = False
                payload["status"] = "degraded"
                payload["database"] = "error"
                payload["error"] = exc.__class__.__name__
                status_code = 503

        if self.check_production_config and not settings.DEBUG:
            issues = []
            if settings.EMAIL_BACKEND.endswith(".smtp.EmailBackend"):
                if not settings.EMAIL_HOST or settings.EMAIL_HOST == "localhost":
                    issues.append("EMAIL_HOST is not configured for production.")
                if not settings.DEFAULT_FROM_EMAIL or "localhost" in settings.DEFAULT_FROM_EMAIL:
                    issues.append("DEFAULT_FROM_EMAIL is not configured for production.")
            if not getattr(settings, "USE_S3_MEDIA_STORAGE", False):
                issues.append("DJANGO_USE_S3_MEDIA_STORAGE is disabled; uploaded media will not be persistent on ephemeral hosts.")
            elif not getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
                issues.append("AWS_STORAGE_BUCKET_NAME is required when S3 media storage is enabled.")
            if not getattr(settings, "STRIPE_SECRET_KEY", ""):
                issues.append("STRIPE_SECRET_KEY is required for production finance operations.")
            if not getattr(settings, "STRIPE_WEBHOOK_SECRET", ""):
                issues.append("STRIPE_WEBHOOK_SECRET is required to verify Stripe webhooks in production.")
            if not getattr(settings, "CARDBOOK_ENABLE_REQUEST_ID_HEADERS", True):
                issues.append("CARDBOOK_ENABLE_REQUEST_ID_HEADERS should remain enabled in production for traceability.")

            payload["production_config"] = "ok" if not issues else "warning"
            if issues:
                payload["success"] = False
                payload["status"] = "degraded"
                payload["production_config_issues"] = issues
                status_code = 503

        return JsonResponse(payload, status=status_code)


class ReadinessView(HealthView):
    check_database = True
    check_production_config = True
