from django.urls import path

from .views import CardClickCreateView, CardStatsView, CardViewCreateView


urlpatterns = [
    path("cards/<int:card_id>/view/", CardViewCreateView.as_view(), name="card-view"),
    path("cards/<int:card_id>/click/", CardClickCreateView.as_view(), name="card-click"),
    path("cards/<int:card_id>/stats/", CardStatsView.as_view(), name="card-stats"),
]
