from django.urls import include, path

from .views import (
    BusinessCardCreateView,
    BusinessCardDeleteView,
    BusinessCardUpdateView,
    BookDeleteView,
    CardCreateView,
    CardDeleteView,
    CardUpdateView,
    CompanyCreateView,
    CompanyDeleteView,
    CompanyUpdateView,
    DashboardAnalyticsView,
    DashboardBusinessCardsView,
    DashboardBookView,
    DashboardCardsView,
    DashboardCompaniesView,
    DashboardHomeView,
)
from websitebuilder.views import DashboardWebsiteBuilderView, DashboardWebsitePreviewView
from referrals.views import NotificationInboxView, ReferralDashboardView
from jobcards.views import DashboardDeleteSavedJobCardView, DashboardSaveJobCardView, DashboardWhiteCardJobView
from accesscontrol.views import DashboardAccessControlView


urlpatterns = [
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
    path("", include("forms_builder.dashboard_urls")),
    path("ai-agents/", include("ai_agents.urls")),
    path("companies/", DashboardCompaniesView.as_view(), name="dashboard-companies"),
    path("companies/new/", CompanyCreateView.as_view(), name="dashboard-company-create"),
    path("companies/<int:pk>/edit/", CompanyUpdateView.as_view(), name="dashboard-company-update"),
    path("companies/<int:pk>/delete/", CompanyDeleteView.as_view(), name="dashboard-company-delete"),
    path("companies/<int:company_id>/website/", DashboardWebsiteBuilderView.as_view(), name="dashboard-company-website"),
    path("companies/<int:company_id>/website/preview/", DashboardWebsitePreviewView.as_view(), name="dashboard-company-website-preview"),
    path("companies/<int:company_id>/website/preview/pages/<int:page_id>/", DashboardWebsitePreviewView.as_view(), name="dashboard-company-website-page-preview"),
    path("cards/", DashboardCardsView.as_view(), name="dashboard-cards"),
    path("cards/new/", CardCreateView.as_view(), name="dashboard-card-create"),
    path("cards/<int:pk>/edit/", CardUpdateView.as_view(), name="dashboard-card-update"),
    path("cards/<int:pk>/delete/", CardDeleteView.as_view(), name="dashboard-card-delete"),
    path("business-cards/", DashboardBusinessCardsView.as_view(), name="dashboard-business-cards"),
    path("business-cards/new/", BusinessCardCreateView.as_view(), name="dashboard-business-card-create"),
    path("business-cards/<int:pk>/edit/", BusinessCardUpdateView.as_view(), name="dashboard-business-card-update"),
    path("business-cards/<int:pk>/delete/", BusinessCardDeleteView.as_view(), name="dashboard-business-card-delete"),
    path("white-card-job/", DashboardWhiteCardJobView.as_view(), name="dashboard-white-card-job"),
    path("white-card-job/save/<int:pk>/", DashboardSaveJobCardView.as_view(), name="dashboard-jobcard-save"),
    path("white-card-job/saved/<int:pk>/delete/", DashboardDeleteSavedJobCardView.as_view(), name="dashboard-jobcard-saved-delete"),
    path("book/", DashboardBookView.as_view(), name="dashboard-book"),
    path("book/<int:pk>/delete/", BookDeleteView.as_view(), name="dashboard-book-delete"),
    path("access-control/", DashboardAccessControlView.as_view(), name="dashboard-access-control"),
    path("notifications/", NotificationInboxView.as_view(), name="dashboard-notifications"),
    path("referrals/", ReferralDashboardView.as_view(), name="dashboard-referrals"),
    path("analytics/", DashboardAnalyticsView.as_view(), name="dashboard-analytics"),
]
