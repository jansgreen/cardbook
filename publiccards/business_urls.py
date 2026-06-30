from django.urls import path

from .views import PublicCompanyDetailView


urlpatterns = [
    path("<slug:slug>/", PublicCompanyDetailView.as_view(), name="public-company-detail"),
]
