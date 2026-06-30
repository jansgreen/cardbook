from django.urls import path

from .views import MobileConfigView, MobileDashboardView


urlpatterns = [
    path("config/", MobileConfigView.as_view(), name="mobile-config"),
    path("dashboard/", MobileDashboardView.as_view(), name="mobile-dashboard"),
]
