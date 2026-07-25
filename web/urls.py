from django.urls import path

from accounts.web_views import AgentApplicationView, RegistrationIntentView, WebLoginView, WebLogoutView, WebRegisterView
from .views import (
    AboutView,
    AndroidApkDownloadView,
    AndroidVersionView,
    AndroidView,
    ContactView,
    HomeView,
    PublicCompaniesView,
    PricingView,
    PrivacyView,
    TermsView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="web-home"),
    path("empresas/", PublicCompaniesView.as_view(), name="web-companies"),
    path("login/", WebLoginView.as_view(), name="web-login"),
    path("register/start/", RegistrationIntentView.as_view(), name="web-register-intent"),
    path("register/agent-application/", AgentApplicationView.as_view(), name="web-agent-application"),
    path("register/", WebRegisterView.as_view(), name="web-register"),
    path("logout/", WebLogoutView.as_view(), name="web-logout"),
    path("about/", AboutView.as_view(), name="web-about"),
    path("pricing/", PricingView.as_view(), name="web-pricing"),
    path("contact/", ContactView.as_view(), name="web-contact"),
    path("privacy/", PrivacyView.as_view(), name="web-privacy"),
    path("terms/", TermsView.as_view(), name="web-terms"),
    path("android/", AndroidView.as_view(), name="web-android"),
    path("android/download/", AndroidApkDownloadView.as_view(), name="web-android-download"),
    path("android/version/", AndroidVersionView.as_view(), name="web-android-version"),
]
