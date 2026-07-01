from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView


ANDROID_VERSION_NAME = "0.3.1"
ANDROID_VERSION_CODE = 4
ANDROID_MIN_SDK = 26
ANDROID_TARGET_SDK = 35


class HomeView(TemplateView):
    template_name = "web/home.html"


class AboutView(TemplateView):
    template_name = "web/about.html"


class PricingView(TemplateView):
    template_name = "web/pricing.html"


class ContactView(TemplateView):
    template_name = "web/contact.html"


class PrivacyView(TemplateView):
    template_name = "web/privacy.html"


class TermsView(TemplateView):
    template_name = "web/terms.html"


class AndroidView(TemplateView):
    template_name = "web/android.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apk_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk"
        context["apk_ready"] = apk_path.exists()
        context["apk_version_name"] = ANDROID_VERSION_NAME
        context["apk_version_code"] = str(ANDROID_VERSION_CODE)
        context["apk_min_sdk"] = str(ANDROID_MIN_SDK)
        context["apk_target_sdk"] = str(ANDROID_TARGET_SDK)
        if apk_path.exists():
            size_mb = apk_path.stat().st_size / (1024 * 1024)
            context["apk_size"] = f"{size_mb:.2f} MB"
            context["apk_updated_at"] = apk_path.stat().st_mtime
        return context


class AndroidApkDownloadView(TemplateView):
    def get(self, request, *args, **kwargs):
        apk_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk"
        if not apk_path.exists():
            raise Http404("El APK de Cardbook aun no ha sido generado.")
        return FileResponse(apk_path.open("rb"), as_attachment=True, filename="cardbook.apk")


class AndroidVersionView(TemplateView):
    def get(self, request, *args, **kwargs):
        apk_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk"
        download_url = request.build_absolute_uri(reverse("web-android-download"))
        page_url = request.build_absolute_uri(reverse("web-android"))
        return JsonResponse(
            {
                "app": "cardbook",
                "package": "com.cardbook.app",
                "latest_version_code": ANDROID_VERSION_CODE,
                "latest_version_name": ANDROID_VERSION_NAME,
                "min_supported_version_code": 3,
                "force_update": False,
                "download_url": download_url,
                "release_page_url": f"{page_url}#build",
                "apk_size": apk_path.stat().st_size if apk_path.exists() else 0,
                "message": "Nueva version de Cardbook disponible.",
                "changelog": [
                    "Mejoras de experiencia Android.",
                    "Correcciones visuales del dashboard.",
                    "Soporte de descarga y actualizacion desde la app.",
                ],
            }
        )
