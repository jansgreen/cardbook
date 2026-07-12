from django.urls import path

from jobcards.views import HiringRecommendationsAPIView, SavedJobCardDeleteAPIView, SavedJobCardListAPIView, SaveJobCardAPIView
from .views import SavedBusinessDetailView, SavedBusinessListCreateView


urlpatterns = [
    path("", SavedBusinessListCreateView.as_view(), name="book-list"),
    path("hiring/", HiringRecommendationsAPIView.as_view(), name="book-hiring"),
    path("saved/", SavedJobCardListAPIView.as_view(), name="book-saved-jobcards"),
    path("save/", SaveJobCardAPIView.as_view(), name="book-save-jobcard"),
    path("save/<int:pk>/", SavedJobCardDeleteAPIView.as_view(), name="book-save-jobcard-delete"),
    path("<int:pk>/", SavedBusinessDetailView.as_view(), name="book-detail"),
]
