from django.urls import path

from .views import SavedBusinessDetailView, SavedBusinessListCreateView


urlpatterns = [
    path("", SavedBusinessListCreateView.as_view(), name="book-list"),
    path("<int:pk>/", SavedBusinessDetailView.as_view(), name="book-detail"),
]
