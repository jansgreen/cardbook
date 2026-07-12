from django.urls import path

from .views import (
    MobileActionsView,
    MobileBookView,
    MobileBootstrapView,
    MobileCardsView,
    MobileCompaniesView,
    MobileConfigView,
    MobileDashboardView,
    MobileJobsView,
    MobileWebsitesView,
)


urlpatterns = [
    path("config/", MobileConfigView.as_view(), name="mobile-config"),
    path("bootstrap/", MobileBootstrapView.as_view(), name="mobile-bootstrap"),
    path("dashboard/", MobileDashboardView.as_view(), name="mobile-dashboard"),
    path("companies/", MobileCompaniesView.as_view(), name="mobile-companies"),
    path("cards/", MobileCardsView.as_view(), name="mobile-cards"),
    path("book/", MobileBookView.as_view(), name="mobile-book"),
    path("jobs/", MobileJobsView.as_view(), name="mobile-jobs"),
    path("websites/", MobileWebsitesView.as_view(), name="mobile-websites"),
    path("actions/", MobileActionsView.as_view(), name="mobile-actions"),
]
