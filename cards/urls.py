from django.urls import path

from translations.views import CardTranslationListCreateView
from .views import (
    BusinessCardDetailView,
    BusinessCardListCreateView,
    CardDetailView,
    CardListCreateView,
    PublicCardDetailView,
)


urlpatterns = [
    path("", CardListCreateView.as_view(), name="card-list"),
    path("business-cards/", BusinessCardListCreateView.as_view(), name="business-card-list"),
    path("business-cards/<int:pk>/", BusinessCardDetailView.as_view(), name="business-card-detail"),
    path("<int:pk>/", CardDetailView.as_view(), name="card-detail"),
    path("<int:card_id>/translations/", CardTranslationListCreateView.as_view(), name="card-translations"),
    path("<slug:slug>/", PublicCardDetailView.as_view(), name="public-card"),
]
