from django.urls import path

from accounts.web_views import WebLoginView, WebLogoutView, WebRegisterView
from .views import AboutView, AndroidApkDownloadView, AndroidView, ContactView, HomeView, PricingView


urlpatterns = [
    path("", HomeView.as_view(), name="web-home"),
    path("login/", WebLoginView.as_view(), name="web-login"),
    path("register/", WebRegisterView.as_view(), name="web-register"),
    path("logout/", WebLogoutView.as_view(), name="web-logout"),
    path("about/", AboutView.as_view(), name="web-about"),
    path("pricing/", PricingView.as_view(), name="web-pricing"),
    path("contact/", ContactView.as_view(), name="web-contact"),
    path("android/", AndroidView.as_view(), name="web-android"),
    path("android/download/", AndroidApkDownloadView.as_view(), name="web-android-download"),
]
