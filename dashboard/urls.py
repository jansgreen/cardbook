from django.urls import path

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


urlpatterns = [
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
    path("companies/", DashboardCompaniesView.as_view(), name="dashboard-companies"),
    path("companies/new/", CompanyCreateView.as_view(), name="dashboard-company-create"),
    path("companies/<int:pk>/edit/", CompanyUpdateView.as_view(), name="dashboard-company-update"),
    path("companies/<int:pk>/delete/", CompanyDeleteView.as_view(), name="dashboard-company-delete"),
    path("cards/", DashboardCardsView.as_view(), name="dashboard-cards"),
    path("cards/new/", CardCreateView.as_view(), name="dashboard-card-create"),
    path("cards/<int:pk>/edit/", CardUpdateView.as_view(), name="dashboard-card-update"),
    path("cards/<int:pk>/delete/", CardDeleteView.as_view(), name="dashboard-card-delete"),
    path("business-cards/", DashboardBusinessCardsView.as_view(), name="dashboard-business-cards"),
    path("business-cards/new/", BusinessCardCreateView.as_view(), name="dashboard-business-card-create"),
    path("business-cards/<int:pk>/edit/", BusinessCardUpdateView.as_view(), name="dashboard-business-card-update"),
    path("business-cards/<int:pk>/delete/", BusinessCardDeleteView.as_view(), name="dashboard-business-card-delete"),
    path("book/", DashboardBookView.as_view(), name="dashboard-book"),
    path("book/<int:pk>/delete/", BookDeleteView.as_view(), name="dashboard-book-delete"),
    path("analytics/", DashboardAnalyticsView.as_view(), name="dashboard-analytics"),
]
