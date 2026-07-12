from django.urls import path

from .views import PublicFormDetailView, PublicFormSubmitView


urlpatterns = [
    path("<slug:company_slug>/<slug:form_slug>/", PublicFormDetailView.as_view(), name="forms-builder-public-detail"),
    path("<slug:company_slug>/<slug:form_slug>/submit/", PublicFormSubmitView.as_view(), name="forms-builder-public-submit"),
]

