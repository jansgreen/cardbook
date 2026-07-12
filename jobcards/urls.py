from django.urls import path

from .views import (
    PublicWhiteCardJobAPIView,
    SpecialtyListAPIView,
    WhiteCardJobListCreateAPIView,
    WhiteCardJobMeAPIView,
)


urlpatterns = [
    path("", WhiteCardJobListCreateAPIView.as_view(), name="jobcard-list"),
    path("me/", WhiteCardJobMeAPIView.as_view(), name="jobcard-me"),
    path("specialties/", SpecialtyListAPIView.as_view(), name="jobcard-specialties"),
    path("<str:username>/", PublicWhiteCardJobAPIView.as_view(), name="jobcard-public-api"),
]
