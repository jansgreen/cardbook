from django.db.models import Count, Q
from django.urls import reverse
from rest_framework import permissions
from rest_framework.views import APIView

from accounts.serializers import ProfileSerializer
from alliances.models import CompanyAlliance
from business_feed.models import BusinessPost
from business_feed.serializers import BusinessPostSerializer
from cards.models import BusinessCard, DigitalCard
from cards.serializers import BusinessCardSerializer, DigitalCardSerializer
from cardbookweb.responses import success_response
from companies.models import Company
from companies.serializers import CompanySerializer
from book.models import SavedBusiness


def absolute_url(request, path_or_url):
    if not path_or_url:
        return ""
    if str(path_or_url).startswith(("http://", "https://")):
        return str(path_or_url)
    return request.build_absolute_uri(path_or_url)


def user_companies_queryset(user):
    return (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
    ).distinct()


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
                "dashboard": request.build_absolute_uri(reverse("mobile-dashboard")),
            },
            "public_base_url": request.build_absolute_uri("/"),
            "media_base_url": request.build_absolute_uri("/media/"),
            "android_version": request.build_absolute_uri(reverse("web-android-version")),
            "android_download": request.build_absolute_uri(reverse("web-android-download")),
        }
        return success_response("Mobile config retrieved successfully.", data)


class MobileDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        company_ids = list(companies.values_list("id", flat=True))

        cards = DigitalCard.objects.filter(is_active=True, company_id__in=company_ids).select_related("company", "user")
        business_cards = BusinessCard.objects.filter(is_active=True, profile__company_id__in=company_ids).select_related(
            "profile",
            "profile__company",
            "profile__user",
        )
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
