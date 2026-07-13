from pathlib import Path
import json

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Count, Q
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.views import APIView

from cards.models import BusinessCard
from cardbookweb.responses import success_response
from companies.models import Company
from jobcards.models import Specialty, WhiteCardJob
from websitebuilder.models import Website
from websitebuilder.services import website_public_url


ANDROID_VERSION_NAME = "0.1.3"
ANDROID_VERSION_CODE = 4
ANDROID_MIN_SDK = 26
ANDROID_TARGET_SDK = 36
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


def get_flutter_aab_info():
    aab_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.aab"
    metadata_path = Path(settings.BASE_DIR) / "static" / "downloads" / "cardbook.aab.json"
    if not aab_path.exists() or not metadata_path.exists():
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None

    if metadata.get("source") != "flutter":
        return None
    if metadata.get("artifact_type") != "aab":
        return None
    if aab_path.stat().st_size < APK_MIN_FLUTTER_SIZE:
        return None

    return {
        "path": aab_path,
        "metadata": metadata,
        "size": aab_path.stat().st_size,
    }


class HomeView(TemplateView):
    template_name = "web/home.html"


class PublicCompaniesView(TemplateView):
    template_name = "web/companies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = (self.request.GET.get("q") or "").strip()
        result_type = (self.request.GET.get("type") or "cards").strip()
        category = (self.request.GET.get("category") or "").strip()
        location = (self.request.GET.get("location") or "").strip()
        job_category = (self.request.GET.get("job_category") or "").strip()
        has_qr = self.request.GET.get("has_qr") == "1"
        has_website = self.request.GET.get("has_website") == "1"
        has_photo = self.request.GET.get("has_photo") == "1"

        business_cards = BusinessCard.objects.filter(
            is_active=True,
            profile__is_active=True,
            profile__company__is_active=True,
        ).select_related(
            "profile",
            "profile__company",
            "profile__user",
        )
        if query:
            business_cards = business_cards.filter(
                Q(display_name__icontains=query)
                | Q(company_name__icontains=query)
                | Q(job_title__icontains=query)
                | Q(email__icontains=query)
                | Q(phone_number__icontains=query)
                | Q(website__icontains=query)
                | Q(services__icontains=query)
                | Q(profile__company__name__icontains=query)
                | Q(profile__company__category__icontains=query)
                | Q(profile__company__city__icontains=query)
                | Q(profile__company__region__icontains=query)
                | Q(profile__company__services__icontains=query)
                | Q(profile__company__description__icontains=query)
            )
        if category:
            business_cards = business_cards.filter(profile__company__category=category)
        if location:
            business_cards = business_cards.filter(
                Q(profile__company__city=location) | Q(profile__company__region=location)
            )
        if job_category:
            business_cards = business_cards.filter(profile__company__job_specialties__specialty__category=job_category)
        if has_qr:
            business_cards = business_cards.filter(include_qr=True)
        if has_website:
            business_cards = business_cards.filter(Q(website__isnull=False) | Q(profile__website__isnull=False)).exclude(
                website="", profile__website=""
            )
        if has_photo:
            business_cards = business_cards.exclude(profile__photo="")

        white_cards = WhiteCardJob.objects.filter(is_active=True, is_available=True).select_related("user", "specialty")
        if query:
            white_cards = white_cards.filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__username__icontains=query)
                | Q(title__icontains=query)
                | Q(specialty__name__icontains=query)
                | Q(specialty__category__icontains=query)
                | Q(short_description__icontains=query)
                | Q(technologies__icontains=query)
                | Q(address__icontains=query)
            )
        if job_category:
            white_cards = white_cards.filter(specialty__category=job_category)
        if location:
            white_cards = white_cards.filter(address__icontains=location)
        if has_photo:
            white_cards = white_cards.exclude(photo="")

        websites = Website.objects.filter(
            is_active=True,
            is_published=True,
            company__is_active=True,
        ).select_related("company", "theme").annotate(page_total=Count("pages", distinct=True))
        if query:
            websites = websites.filter(
                Q(title__icontains=query)
                | Q(meta_title__icontains=query)
                | Q(meta_description__icontains=query)
                | Q(company__name__icontains=query)
                | Q(company__category__icontains=query)
                | Q(company__services__icontains=query)
                | Q(company__description__icontains=query)
                | Q(company__city__icontains=query)
                | Q(company__region__icontains=query)
            )
        if category:
            websites = websites.filter(company__category=category)
        if location:
            websites = websites.filter(Q(company__city=location) | Q(company__region=location))

        show_cards = result_type in ("cards", "all", "companies")
        show_jobs = result_type in ("jobs", "all")
        show_websites = result_type in ("websites", "all")
        company_total = business_cards.values("profile__company").distinct().count()
        context["business_cards"] = (
            business_cards.distinct().order_by("profile__company__name", "display_name") if show_cards else BusinessCard.objects.none()
        )
        context["white_cards"] = white_cards.distinct().order_by("-updated_at") if show_jobs else WhiteCardJob.objects.none()
        context["websites"] = websites.distinct().order_by("company__name", "title") if show_websites else Website.objects.none()
        context["query"] = query
        context["company_total"] = company_total
        context["card_total"] = context["business_cards"].count()
        context["white_card_total"] = context["white_cards"].count()
        context["website_total"] = context["websites"].count()
        context["result_type"] = result_type
        context["selected_category"] = category
        context["selected_location"] = location
        context["selected_job_category"] = job_category
        context["has_qr"] = has_qr
        context["has_website"] = has_website
        context["has_photo"] = has_photo
        context["show_cards"] = show_cards
        context["show_jobs"] = show_jobs
        context["show_websites"] = show_websites
        context["company_categories"] = (
            Company.objects.filter(is_active=True)
            .exclude(category__isnull=True)
            .exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        context["company_locations"] = (
            Company.objects.filter(is_active=True)
            .exclude(city__isnull=True)
            .exclude(city="")
            .order_by("city")
            .values_list("city", flat=True)
            .distinct()
        )
        context["job_categories"] = (
            Specialty.objects.exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        context["filters_active"] = any([result_type != "cards", category, location, job_category, has_qr, has_website, has_photo])
        return context


def business_card_marketplace_item(request, card):
    company = card.company
    return {
        "type": "business_card",
        "id": card.id,
        "title": card.display_name,
        "subtitle": card.job_title or card.profile.job_title or "Perfil profesional",
        "company": company.name,
        "category": company.category,
        "city": company.city,
        "region": company.region,
        "logo": request.build_absolute_uri(company.logo.url) if company.logo else "",
        "photo": request.build_absolute_uri(card.profile.photo.url) if card.profile.photo else "",
        "public_url": request.build_absolute_uri(reverse("public-business-card", kwargs={"slug": card.slug})),
        "qr_svg_url": request.build_absolute_uri(reverse("public-card-qr", kwargs={"slug": card.profile.slug})),
    }


def white_card_marketplace_item(request, card):
    return {
        "type": "white_card_job",
        "id": card.id,
        "title": card.title,
        "subtitle": card.specialty.name if card.specialty_id else "",
        "company": "",
        "category": card.specialty.category if card.specialty_id else "",
        "city": card.address,
        "region": "",
        "logo": "",
        "photo": request.build_absolute_uri(card.photo.url) if card.photo else "",
        "public_url": request.build_absolute_uri(reverse("public-white-card-job", kwargs={"username": card.username})),
        "qr_svg_url": request.build_absolute_uri(reverse("public-white-card-job-qr", kwargs={"username": card.username})),
    }


def website_marketplace_item(request, website):
    return {
        "type": "website",
        "id": website.id,
        "title": website.title,
        "subtitle": website.meta_description or website.company.description,
        "company": website.company.name,
        "category": website.company.category,
        "city": website.company.city,
        "region": website.company.region,
        "logo": request.build_absolute_uri(website.company.logo.url) if website.company.logo else "",
        "photo": request.build_absolute_uri(website.logo.url) if website.logo else "",
        "public_url": website_public_url(request, website),
        "qr_svg_url": "",
    }


class PublicMarketplaceAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        try:
            limit = int(request.query_params.get("limit") or 24)
        except (TypeError, ValueError):
            limit = 24
        limit = max(1, min(limit, 60))

        cards = BusinessCard.objects.filter(is_active=True, profile__is_active=True, profile__company__is_active=True).select_related(
            "profile",
            "profile__company",
            "profile__user",
        )
        jobs = WhiteCardJob.objects.filter(is_active=True, is_available=True).select_related("user", "specialty")
        websites = Website.objects.filter(is_active=True, is_published=True, company__is_active=True).select_related("company", "theme")

        if query:
            cards = cards.filter(
                Q(display_name__icontains=query)
                | Q(company_name__icontains=query)
                | Q(services__icontains=query)
                | Q(profile__company__name__icontains=query)
                | Q(profile__company__category__icontains=query)
                | Q(profile__company__services__icontains=query)
            )
            jobs = jobs.filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(title__icontains=query)
                | Q(specialty__name__icontains=query)
                | Q(specialty__category__icontains=query)
                | Q(short_description__icontains=query)
            )
            websites = websites.filter(
                Q(title__icontains=query)
                | Q(company__name__icontains=query)
                | Q(company__category__icontains=query)
                | Q(company__services__icontains=query)
                | Q(company__description__icontains=query)
            )

        data = {
            "summary": {
                "business_cards": cards.count(),
                "white_card_jobs": jobs.count(),
                "websites": websites.count(),
            },
            "business_cards": [business_card_marketplace_item(request, item) for item in cards.order_by("profile__company__name", "display_name")[:limit]],
            "white_card_jobs": [white_card_marketplace_item(request, item) for item in jobs.order_by("-updated_at")[:limit]],
            "websites": [website_marketplace_item(request, item) for item in websites.order_by("company__name", "title")[:limit]],
        }
        return success_response("Marketplace retrieved successfully.", data)


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
        aab_info = get_flutter_aab_info()
        metadata = apk_info["metadata"] if apk_info else {}
        aab_metadata = aab_info["metadata"] if aab_info else {}
        context["apk_ready"] = apk_info is not None
        context["aab_ready"] = aab_info is not None
        context["apk_version_name"] = metadata.get("version_name", ANDROID_VERSION_NAME)
        context["apk_version_code"] = str(metadata.get("version_code", ANDROID_VERSION_CODE))
        context["apk_min_sdk"] = str(ANDROID_MIN_SDK)
        context["apk_target_sdk"] = str(ANDROID_TARGET_SDK)
        context["apk_build_type"] = metadata.get("build_type", "release")
        context["apk_signing"] = metadata.get("signing", "unknown")
        context["apk_release_signed"] = bool(metadata.get("release_signed", False))
        context["apk_sha256"] = metadata.get("sha256", "")
        context["aab_signing"] = aab_metadata.get("signing", "pending")
        context["aab_release_signed"] = bool(aab_metadata.get("release_signed", False))
        context["play_store_ready"] = context["apk_release_signed"] and context["aab_ready"] and context["aab_release_signed"]
        if apk_info:
            size_mb = apk_info["size"] / (1024 * 1024)
            context["apk_size"] = f"{size_mb:.2f} MB"
            context["apk_updated_at"] = apk_info["path"].stat().st_mtime
        if aab_info:
            aab_size_mb = aab_info["size"] / (1024 * 1024)
            context["aab_size"] = f"{aab_size_mb:.2f} MB"
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
        aab_info = get_flutter_aab_info()
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
                "build_type": metadata.get("build_type", "pending"),
                "signing": metadata.get("signing", "unknown"),
                "release_signed": bool(metadata.get("release_signed", False)),
                "play_store_ready": bool(metadata.get("release_signed", False)) and bool(aab_info),
                "aab_available": aab_info is not None,
                "aab_size": aab_info["size"] if aab_info else 0,
                "sha256": metadata.get("sha256", ""),
                "message": "Nueva version de Cardbook disponible.",
                "changelog": [
                    "Aplicacion Flutter nativa conectada a la API REST.",
                    "Dashboard movil nativo.",
                    "Soporte de actualizacion desde la app.",
                ],
            }
        )
