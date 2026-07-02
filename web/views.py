from pathlib import Path
import json

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView


ANDROID_VERSION_NAME = "0.3.1"
ANDROID_VERSION_CODE = 4
ANDROID_MIN_SDK = 26
ANDROID_TARGET_SDK = 35
APK_MIN_FLUTTER_SIZE = 5 * 1024 * 1024


def get_flutter_apk_info():
    apk_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk"
    metadata_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk.json"
    if not apk_path.exists() or not metadata_path.exists():
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None

    if metadata.get("source") != "flutter":
        return None
    if apk_path.stat().st_size < APK_MIN_FLUTTER_SIZE:
        return None

    return {
        "path": apk_path,
        "metadata": metadata,
        "size": apk_path.stat().st_size,
    }


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
        apk_info = get_flutter_apk_info()
        metadata = apk_info["metadata"] if apk_info else {}
        context["apk_ready"] = apk_info is not None
        context["apk_version_name"] = metadata.get("version_name", ANDROID_VERSION_NAME)
        context["apk_version_code"] = str(metadata.get("version_code", ANDROID_VERSION_CODE))
        context["apk_min_sdk"] = str(ANDROID_MIN_SDK)
        context["apk_target_sdk"] = str(ANDROID_TARGET_SDK)
        if apk_info:
            size_mb = apk_info["size"] / (1024 * 1024)
            context["apk_size"] = f"{size_mb:.2f} MB"
            context["apk_updated_at"] = apk_info["path"].stat().st_mtime
        return context


class AndroidApkDownloadView(TemplateView):
    def get(self, request, *args, **kwargs):
        apk_info = get_flutter_apk_info()
        if not apk_info:
            raise Http404("El APK Flutter de Cardbook aun no ha sido generado.")
        return FileResponse(apk_info["path"].open("rb"), as_attachment=True, filename="cardbook.apk")


class AndroidVersionView(TemplateView):
    def get(self, request, *args, **kwargs):
        apk_info = get_flutter_apk_info()
        metadata = apk_info["metadata"] if apk_info else {}
        download_url = request.build_absolute_uri(reverse("web-android-download"))
        page_url = request.build_absolute_uri(reverse("web-android"))
        return JsonResponse(
            {
                "app": "cardbook",
                "package": "com.cardbook.app",
                "available": apk_info is not None,
                "latest_version_code": metadata.get("version_code", ANDROID_VERSION_CODE),
                "latest_version_name": metadata.get("version_name", ANDROID_VERSION_NAME),
                "min_supported_version_code": 1,
                "force_update": False,
                "download_url": download_url if apk_info else "",
                "release_page_url": f"{page_url}#build",
                "apk_size": apk_info["size"] if apk_info else 0,
                "source": metadata.get("source", "pending"),
                "message": "Nueva version de Cardbook disponible.",
                "changelog": [
                    "Aplicacion Flutter nativa conectada a la API REST.",
                    "Dashboard movil nativo.",
                    "Soporte de actualizacion desde la app.",
                ],
            }
        )
