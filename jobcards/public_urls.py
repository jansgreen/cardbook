from django.urls import path

from .views import PublicWhiteCardJobView, white_card_job_qr_svg


urlpatterns = [
    path("<str:username>/qr.svg", white_card_job_qr_svg, name="public-white-card-job-qr"),
    path("<str:username>/", PublicWhiteCardJobView.as_view(), name="public-white-card-job"),
]
