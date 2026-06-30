from django.urls import path

from .views import BusinessPostDetailView, BusinessPostExcellentView, BusinessPostListCreateView


urlpatterns = [
    path("", BusinessPostListCreateView.as_view(), name="business-post-list"),
    path("<int:pk>/", BusinessPostDetailView.as_view(), name="business-post-detail"),
    path("<int:pk>/excellent/", BusinessPostExcellentView.as_view(), name="business-post-excellent"),
]
