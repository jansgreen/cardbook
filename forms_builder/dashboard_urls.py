from django.urls import path

from .views import (
    DashboardAttachFormToSectionView,
    DashboardFieldCreateView,
    DashboardFieldDeleteView,
    DashboardFieldUpdateView,
    DashboardFormCreateView,
    DashboardFormDeleteView,
    DashboardFormDetailView,
    DashboardFormListView,
    DashboardFormUpdateView,
)


urlpatterns = [
    path("companies/<int:company_id>/forms/", DashboardFormListView.as_view(), name="dashboard-form-builder-list"),
    path("companies/<int:company_id>/forms/create/", DashboardFormCreateView.as_view(), name="dashboard-form-builder-create"),
    path("companies/<int:company_id>/forms/<int:form_id>/", DashboardFormDetailView.as_view(), name="dashboard-form-builder-detail"),
    path("companies/<int:company_id>/forms/<int:form_id>/update/", DashboardFormUpdateView.as_view(), name="dashboard-form-builder-update"),
    path("companies/<int:company_id>/forms/<int:form_id>/delete/", DashboardFormDeleteView.as_view(), name="dashboard-form-builder-delete"),
    path("companies/<int:company_id>/forms/<int:form_id>/fields/create/", DashboardFieldCreateView.as_view(), name="dashboard-form-field-create"),
    path("companies/<int:company_id>/forms/<int:form_id>/fields/<int:field_id>/update/", DashboardFieldUpdateView.as_view(), name="dashboard-form-field-update"),
    path("companies/<int:company_id>/forms/<int:form_id>/fields/<int:field_id>/delete/", DashboardFieldDeleteView.as_view(), name="dashboard-form-field-delete"),
    path("companies/<int:company_id>/forms/<int:form_id>/attach-section/", DashboardAttachFormToSectionView.as_view(), name="dashboard-form-attach-section"),
]
