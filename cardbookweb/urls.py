from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from .health import HealthView, ReadinessView
from web.views import PublicMarketplaceAPIView


def api_root(request):
    return JsonResponse({
        "success": True,
        "message": "Cardbook API is running.",
        "data": {
            "api_version": "v1",
            "accounts": "/api/v1/accounts/",
            "companies": "/api/v1/companies/",
            "cards": "/api/v1/cards/",
            "analytics": "/api/v1/analytics/",
            "posts": "/api/v1/posts/",
            "alliances": "/api/v1/alliances/",
            "book": "/api/v1/book/",
            "jobcards": "/api/v1/jobcards/",
            "mobile": "/api/v1/mobile/",
            "marketplace": "/api/v1/marketplace/",
            "websites": "/api/v1/websites/",
            "public_sites": "/api/v1/public-sites/",
            "referrals": "/api/v1/referrals/",
            "finance": "/api/v1/finance/overview/",
            "billing": "/api/v1/billing/subscription/",
            "agent_finance": "/api/v1/agent/overview/",
            "support": "/api/v1/support/tickets/",
            "push": "/api/v1/push/devices/",
            "ai_agents": "/api/v1/ai-agents/",
            "recommendations": "/api/v1/companies/recommendations/",
            "admin": "/admin/",
        },
    })


urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("health/ready/", ReadinessView.as_view(), name="health-ready"),
    path("admin/", admin.site.urls),
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/companies/", include("companies.urls")),
    path("api/v1/cards/", include("cards.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
    path("api/v1/posts/", include("business_feed.urls")),
    path("api/v1/alliances/", include("alliances.urls")),
    path("api/v1/book/", include("book.urls")),
    path("api/v1/jobcards/", include("jobcards.urls")),
    path("api/v1/mobile/", include("mobile.urls")),
    path("api/v1/marketplace/", PublicMarketplaceAPIView.as_view(), name="api-marketplace"),
    path("api/v1/", include("websitebuilder.api_urls")),
    path("api/v1/referrals/", include("referrals.urls")),
    path("api/v1/support/", include("support.urls")),
    path("api/v1/push/", include("pushnotifications.urls")),
    path("api/v1/ai-agents/", include("ai_agents.api_urls")),
    path("", include("financial_analytics.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("forms/", include("forms_builder.urls")),
    path("ai/", include("ai_agents.public_urls")),
    path("site/", include("websitebuilder.urls")),
    path("business/", include("publiccards.business_urls")),
    path("job/", include("jobcards.public_urls")),
    path("c/", include("publiccards.urls")),
    path("", include("web.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
