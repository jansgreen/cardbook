from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "web/home.html"


class AboutView(TemplateView):
    template_name = "web/about.html"


class PricingView(TemplateView):
    template_name = "web/pricing.html"


class ContactView(TemplateView):
    template_name = "web/contact.html"


class AndroidView(TemplateView):
    template_name = "web/android.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apk_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.apk"
        context["apk_ready"] = apk_path.exists()
        context["apk_version_name"] = "0.3.0"
        context["apk_version_code"] = "3"
        context["apk_min_sdk"] = "26"
        context["apk_target_sdk"] = "35"
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
