from django.urls import path

from memberships.views import CompanyMemberDetailView, CompanyMemberListCreateView
from company_ratings.views import CompanyRatingView
from .views import CompanyDetailView, CompanyListCreateView, CompanyRecommendationView


urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list"),
    path("recommendations/", CompanyRecommendationView.as_view(), name="company-recommendations"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<int:company_id>/rating/", CompanyRatingView.as_view(), name="company-rating"),
    path("<int:company_id>/members/", CompanyMemberListCreateView.as_view(), name="company-members"),
    path("<int:company_id>/members/<int:member_id>/", CompanyMemberDetailView.as_view(), name="company-member-detail"),
]
