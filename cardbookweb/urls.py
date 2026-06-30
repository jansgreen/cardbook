from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


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
            "recommendations": "/api/v1/companies/recommendations/",
            "admin": "/admin/",
        },
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/companies/", include("companies.urls")),
    path("api/v1/cards/", include("cards.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
    path("api/v1/posts/", include("business_feed.urls")),
    path("api/v1/alliances/", include("alliances.urls")),
    path("api/v1/book/", include("book.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("business/", include("publiccards.business_urls")),
    path("c/", include("publiccards.urls")),
    path("", include("web.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
