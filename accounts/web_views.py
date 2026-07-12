from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView

from referrals.services import register_referral_source
from .forms import WebLoginForm, WebRegisterForm


class WebLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = WebLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("dashboard-home")


class WebRegisterView(CreateView):
    form_class = WebRegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard-home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard-home")
        referral_code = request.GET.get("ref")
        if referral_code:
            request.session["referral_code"] = referral_code
            request.session["referral_source_url"] = request.build_absolute_uri()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        referral_code = self.request.session.pop("referral_code", "")
        source_url = self.request.session.pop("referral_source_url", "")
        if referral_code:
            try:
                register_referral_source(user=self.object, referral_code=referral_code, request=self.request, source_url=source_url)
            except ValueError:
                pass
        login(self.request, self.object)
        return response


class WebLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("web-home")

    def post(self, request):
        logout(request)
        return redirect("web-home")
