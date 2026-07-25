from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView

from referrals.models import AgentApplication
from referrals.services import register_referral_source
from dashboard.access_policy import default_dashboard_url
from .forms import AgentApplicationForm, RegistrationIntentForm, WebLoginForm, WebRegisterForm
from .models import Profile


class WebLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = WebLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or default_dashboard_url(self.request.user)


class RegistrationIntentView(FormView):
    template_name = "accounts/register_intent.html"
    form_class = RegistrationIntentForm
    success_url = reverse_lazy("web-register")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(default_dashboard_url(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usage = form.cleaned_data["usage"]
        referral_code = form.cleaned_data.get("referral_code", "")
        self.request.session["registration_intent"] = usage

        if usage == Profile.INTENT_AGENT:
            if referral_code:
                self.request.session["referral_code"] = referral_code
                self.request.session["referral_source_url"] = self.request.build_absolute_uri()
                return super().form_valid(form)
            return redirect("web-agent-application")

        self.request.session.pop("referral_code", None)
        self.request.session.pop("referral_source_url", None)
        return super().form_valid(form)


class AgentApplicationView(FormView):
    template_name = "accounts/agent_application.html"
    form_class = AgentApplicationForm
    success_url = reverse_lazy("web-register")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(default_dashboard_url(request.user))
        request.session["registration_intent"] = Profile.INTENT_AGENT
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        application = AgentApplication.objects.create(**form.cleaned_data)
        self.request.session["agent_application"] = {
            "id": application.id,
            "full_name": application.full_name,
            "email": application.email,
            "phone_number": application.phone_number,
        }
        return super().form_valid(form)


class WebRegisterView(CreateView):
    form_class = WebRegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard-home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(default_dashboard_url(request.user))
        referral_code = request.GET.get("ref")
        if referral_code:
            request.session["referral_code"] = referral_code
            request.session["referral_source_url"] = request.build_absolute_uri()
            request.session["registration_intent"] = Profile.INTENT_AGENT
        if not request.session.get("registration_intent") and not referral_code:
            return redirect("web-register-intent")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        agent_application = self.request.session.get("agent_application", {})
        if agent_application:
            full_name = agent_application.get("full_name", "").strip().split(" ", 1)
            initial["first_name"] = full_name[0] if full_name else ""
            initial["last_name"] = full_name[1] if len(full_name) > 1 else ""
            initial["email"] = agent_application.get("email", "")
            initial["phone_number"] = agent_application.get("phone_number", "")
        return initial

    def form_valid(self, form):
        self.object = form.save()
        self.object.registration_intent = self.request.session.pop("registration_intent", "")
        if self.object.registration_intent:
            self.object.save(update_fields=["registration_intent"])
        referral_code = self.request.session.pop("referral_code", "")
        source_url = self.request.session.pop("referral_source_url", "")
        self.request.session.pop("agent_application", None)
        if referral_code:
            try:
                register_referral_source(user=self.object, referral_code=referral_code, request=self.request, source_url=source_url)
            except ValueError:
                pass
        login(self.request, self.object)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return default_dashboard_url(self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registration_intent"] = self.request.session.get("registration_intent", "")
        return context


class WebLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("web-home")

    def post(self, request):
        logout(request)
        return redirect("web-home")
