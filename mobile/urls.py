from django.urls import path

from .views import (
    MobileActionsView,
    MobileAIAgentsView,
    MobileBookView,
    MobileBootstrapView,
    MobileCardsView,
    MobileCompaniesView,
    MobileConfigView,
    MobileDashboardView,
    MobileFormsView,
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
    path("forms/", MobileFormsView.as_view(), name="mobile-forms"),
    path("ai-agents/", MobileAIAgentsView.as_view(), name="mobile-ai-agents"),
    path("actions/", MobileActionsView.as_view(), name="mobile-actions"),
]
