from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView

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
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class WebLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("web-home")

    def post(self, request):
        logout(request)
        return redirect("web-home")
