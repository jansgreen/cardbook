from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views import View


class HealthView(View):
    check_database = False

    def get(self, request, *args, **kwargs):
        payload = {
            "success": True,
            "service": "cardbook",
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.DEPLOY_ENV,
            "commit": settings.RELEASE_COMMIT[:12] if settings.RELEASE_COMMIT else "unknown",
            "debug": settings.DEBUG,
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

        return JsonResponse(payload, status=status_code)


class ReadinessView(HealthView):
    check_database = True
