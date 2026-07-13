from django.db.models import Count, Q
from django.urls import reverse
from rest_framework import permissions
from rest_framework.views import APIView

from accounts.serializers import ProfileSerializer
from alliances.models import CompanyAlliance
from book.models import SavedBusiness
from book.serializers import SavedBusinessSerializer
from business_feed.models import BusinessPost
from business_feed.serializers import BusinessPostSerializer
from cards.serializers import BusinessCardSerializer, DigitalCardSerializer
from cards.services import profile_creation_companies, visible_business_cards_queryset, visible_profiles_queryset
from cardbookweb.responses import StandardPagination, success_response
from companies.models import Company
from companies.permissions import can_manage_company
from companies.serializers import CompanySerializer
from jobcards.models import SavedJobCard, WhiteCardJob
from jobcards.serializers import SavedJobCardSerializer, WhiteCardJobSerializer
from jobcards.services import get_company_for_user, recommended_job_cards, user_active_job_card
from websitebuilder.models import Website
from websitebuilder.serializers import WebsiteSerializer
from websitebuilder.services import can_manage_website_builder, can_publish_website_builder


def absolute_url(request, path_or_url):
    if not path_or_url:
        return ""
    if str(path_or_url).startswith(("http://", "https://")):
        return str(path_or_url)
    return request.build_absolute_uri(path_or_url)


def user_companies_queryset(user):
    return profile_creation_companies(user)


def paginate_response(request, queryset, serializer_class):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def mobile_endpoints(request):
    return {
        "config": request.build_absolute_uri(reverse("mobile-config")),
        "bootstrap": request.build_absolute_uri(reverse("mobile-bootstrap")),
        "dashboard": request.build_absolute_uri(reverse("mobile-dashboard")),
        "companies": request.build_absolute_uri(reverse("mobile-companies")),
        "cards": request.build_absolute_uri(reverse("mobile-cards")),
        "book": request.build_absolute_uri(reverse("mobile-book")),
        "jobs": request.build_absolute_uri(reverse("mobile-jobs")),
        "websites": request.build_absolute_uri(reverse("mobile-websites")),
            "actions": request.build_absolute_uri(reverse("mobile-actions")),
            "push_devices": request.build_absolute_uri(reverse("push-devices")),
            "push_test": request.build_absolute_uri(reverse("push-test")),
    }


def crud_links(request):
    return {
        "companies": request.build_absolute_uri(reverse("company-list")),
        "digital_cards": request.build_absolute_uri(reverse("card-list")),
        "business_cards": request.build_absolute_uri(reverse("business-card-list")),
        "book": request.build_absolute_uri(reverse("book-list")),
        "jobcards": request.build_absolute_uri(reverse("jobcard-list")),
        "jobcard_me": request.build_absolute_uri(reverse("jobcard-me")),
        "websites": request.build_absolute_uri(reverse("api-website-list")),
    }


class MobileConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            "app": "cardbook",
            "api_version": "v1",
            "platforms": ["android", "ios"],
            "auth": {
                "login": request.build_absolute_uri(reverse("login")),
                "register": request.build_absolute_uri(reverse("register")),
                "refresh": request.build_absolute_uri(reverse("token-refresh")),
                "verify": request.build_absolute_uri(reverse("token-verify")),
                "me": request.build_absolute_uri(reverse("account-me")),
            },
            "mobile": {
                **mobile_endpoints(request),
            },
            "crud": crud_links(request),
            "public_base_url": request.build_absolute_uri("/"),
            "media_base_url": request.build_absolute_uri("/media/"),
            "android_version": request.build_absolute_uri(reverse("web-android-version")),
            "android_download": request.build_absolute_uri(reverse("web-android-download")),
            "push": {
                "devices": request.build_absolute_uri(reverse("push-devices")),
                "disable": request.build_absolute_uri(reverse("push-device-disable")),
                "test": request.build_absolute_uri(reverse("push-test")),
            },
        }
        return success_response("Mobile config retrieved successfully.", data)


class MobileBootstrapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        active_company = companies.first()
        data = {
            "user": ProfileSerializer(request.user, context={"request": request}).data,
            "endpoints": mobile_endpoints(request),
            "crud": crud_links(request),
            "capabilities": {
                "can_create_company": True,
                "can_create_digital_card": companies.exists(),
                "can_create_business_card": visible_profiles_queryset(request.user).exists(),
                "can_create_white_card_job": not Company.objects.filter(is_active=True, owner=request.user).exists() or bool(user_active_job_card(request.user)),
                "can_manage_active_company": can_manage_company(request.user, active_company) if active_company else False,
                "can_manage_website": can_manage_website_builder(request.user, active_company) if active_company else False,
                "can_publish_website": can_publish_website_builder(request.user, active_company) if active_company else False,
            },
            "navigation": [
                {"key": "home", "label": "Inicio", "endpoint": mobile_endpoints(request)["dashboard"]},
                {"key": "companies", "label": "Empresas", "endpoint": mobile_endpoints(request)["companies"]},
                {"key": "cards", "label": "Tarjetas", "endpoint": mobile_endpoints(request)["cards"]},
                {"key": "book", "label": "Book", "endpoint": mobile_endpoints(request)["book"]},
                {"key": "jobs", "label": "White Card Jobs", "endpoint": mobile_endpoints(request)["jobs"]},
                {"key": "websites", "label": "Websites", "endpoint": mobile_endpoints(request)["websites"]},
            ],
        }
        return success_response("Mobile bootstrap retrieved successfully.", data)


class MobileDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        company_ids = list(companies.values_list("id", flat=True))

        cards = visible_profiles_queryset(request.user)
        business_cards = visible_business_cards_queryset(request.user)
        posts = BusinessPost.objects.filter(is_active=True, company_id__in=company_ids).select_related("company").annotate(
            excellent_count=Count("excellents", distinct=True)
        )
        alliances = CompanyAlliance.objects.filter(Q(requester_id__in=company_ids) | Q(receiver_id__in=company_ids))
        accepted_alliances = alliances.filter(status=CompanyAlliance.STATUS_ACCEPTED)
        pending_alliances = alliances.filter(status=CompanyAlliance.STATUS_PENDING)

        suggested_companies = (
            Company.objects.filter(is_active=True)
            .exclude(id__in=company_ids)
            .annotate(efficient_total=Count("ratings", distinct=True))
            .order_by("-efficient_total", "name")[:5]
        )

        total_views = sum(card.views.count() for card in cards)
        total_clicks = sum(card.clicks.count() for card in cards)

        data = {
            "user": ProfileSerializer(request.user, context={"request": request}).data,
            "summary": {
                "companies": companies.count(),
                "digital_cards": cards.count(),
                "business_cards": business_cards.count(),
                "book_items": SavedBusiness.objects.filter(user=request.user).count(),
                "posts": posts.count(),
                "alliances": accepted_alliances.count(),
                "pending_alliances": pending_alliances.count(),
                "views": total_views,
                "clicks": total_clicks,
                "excellent": sum(company.efficient_count for company in companies),
                "notifications": pending_alliances.count(),
            },
            "companies": CompanySerializer(companies.annotate(efficient_total=Count("ratings", distinct=True))[:5], many=True, context={"request": request}).data,
            "digital_cards": DigitalCardSerializer(cards[:5], many=True, context={"request": request}).data,
            "business_cards": BusinessCardSerializer(business_cards[:5], many=True, context={"request": request}).data,
            "recent_posts": BusinessPostSerializer(posts[:5], many=True, context={"request": request}).data,
            "suggested_companies": CompanySerializer(suggested_companies, many=True, context={"request": request}).data,
            "quick_links": {
                "companies": request.build_absolute_uri("/api/v1/companies/"),
                "cards": request.build_absolute_uri("/api/v1/cards/"),
                "business_cards": request.build_absolute_uri("/api/v1/cards/business-cards/"),
                "posts": request.build_absolute_uri("/api/v1/posts/"),
                "alliances": request.build_absolute_uri("/api/v1/alliances/"),
                "book": request.build_absolute_uri("/api/v1/book/"),
            },
        }
        return success_response("Mobile dashboard retrieved successfully.", data)


class MobileCompaniesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user).annotate(efficient_total=Count("ratings", distinct=True)).order_by("name", "id")
        return paginate_response(request, companies, CompanySerializer)


class MobileCardsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        digital_cards = visible_profiles_queryset(request.user)
        business_cards = visible_business_cards_queryset(request.user)
        data = {
            "digital_cards": DigitalCardSerializer(digital_cards, many=True, context={"request": request}).data,
            "business_cards": BusinessCardSerializer(business_cards, many=True, context={"request": request}).data,
            "create_links": {
                "digital_card": request.build_absolute_uri(reverse("card-list")),
                "business_card": request.build_absolute_uri(reverse("business-card-list")),
            },
        }
        return success_response("Mobile cards retrieved successfully.", data)


class MobileBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_company = get_company_for_user(request.user, request.query_params.get("company"))
        business_items = SavedBusiness.objects.filter(user=request.user).select_related(
            "company",
            "digital_card__company",
            "digital_card__user",
            "business_card__profile__company",
            "business_card__profile__user",
        )
        saved_candidates = (
            SavedJobCard.objects.filter(company=active_company).select_related("company", "job_card__user", "job_card__specialty", "saved_by")
            if active_company else SavedJobCard.objects.none()
        )
        data = {
            "active_company": CompanySerializer(active_company, context={"request": request}).data if active_company else None,
            "businesses": SavedBusinessSerializer(business_items, many=True, context={"request": request}).data,
            "saved_candidates": SavedJobCardSerializer(saved_candidates, many=True, context={"request": request}).data,
            "recommendations": WhiteCardJobSerializer(recommended_job_cards(active_company, limit=8), many=True, context={"request": request}).data if active_company else [],
        }
        return success_response("Mobile book retrieved successfully.", data)


class MobileJobsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = get_company_for_user(request.user, request.query_params.get("company"))
        my_card = user_active_job_card(request.user)
        public_jobs = WhiteCardJob.objects.filter(is_active=True, is_available=True).select_related("user", "specialty")
        specialty = request.query_params.get("specialty")
        if specialty:
            public_jobs = public_jobs.filter(specialty__slug=specialty)
        data = {
            "my_card": WhiteCardJobSerializer(my_card, context={"request": request}).data if my_card else None,
            "available_jobs": WhiteCardJobSerializer(public_jobs[:30], many=True, context={"request": request}).data,
            "recommended_for_company": WhiteCardJobSerializer(recommended_job_cards(company, limit=8), many=True, context={"request": request}).data if company else [],
        }
        return success_response("Mobile jobs retrieved successfully.", data)


class MobileWebsitesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        websites = Website.objects.filter(company__in=companies, is_active=True).select_related("company", "theme")
        data = {
            "websites": WebsiteSerializer(websites, many=True, context={"request": request}).data,
            "create_link": request.build_absolute_uri(reverse("api-website-list")),
        }
        return success_response("Mobile websites retrieved successfully.", data)


class MobileActionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {
            "native_actions": {
                "phone": "tel:{value}",
                "email": "mailto:{value}",
                "website": "{value}",
                "whatsapp": "https://wa.me/{value}",
                "maps": "https://www.google.com/maps/search/?api=1&query={value}",
                "share": "system_share",
                "download_contact": "vcf",
                "download_qr": "image_svg",
            },
            "share_templates": {
                "digital_card": "Conecta conmigo en Cardbook: {public_url}",
                "business_card": "Te comparto mi tarjeta de presentacion: {public_url}",
                "white_card_job": "Mira mi White Card Job en Cardbook: {public_url}",
                "company": "Conoce esta empresa en Cardbook: {public_url}",
            },
        }
        return success_response("Mobile actions retrieved successfully.", data)
