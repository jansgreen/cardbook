from django.urls import path

from .views import AllianceDecisionView, AllianceListCreateView


urlpatterns = [
    path("", AllianceListCreateView.as_view(), name="alliance-list"),
    path("<int:pk>/<str:decision>/", AllianceDecisionView.as_view(), name="alliance-decision"),
]
