from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView, View

from analytics.models import CardClick, CardView
from ai_agents.services import business_assistant_context
from alliances.models import CompanyAlliance
from book.models import SavedBusiness
from business_feed.models import BusinessPost, BusinessPostExcellent
from cards.models import BusinessCard, DigitalCard
from cards.services import (
    can_manage_business_profile,
    can_use_profile_for_business_card,
    visible_business_cards_queryset,
    visible_profiles_queryset,
)
from companies.models import Company
from companies.permissions import can_access_company, can_manage_company
from company_ratings.models import CompanyRating
from jobcards.models import SavedJobCard
from jobcards.services import get_company_for_user, recommended_job_cards
from memberships.models import CompanyMember
from referrals.models import AgentProfile
from referrals.services import record_agent_card_sale
from subscriptions.models import Subscription
from accesscontrol.services import PERM_MANAGE_PLATFORM_USERS, PERM_MANAGE_STRIPE_CONFIGURATION, ensure_default_permissions, user_has_access_permission
from accounts.models import Profile
from billing.models import StripeConfiguration
from financial_analytics.services import FinanceConfigurationError, create_subscription_checkout_session
from .forms import AccountPlanForm, AccountSettingsForm, BusinessCardForm, BusinessPostForm, CompanyForm, DigitalCardForm, PlatformUserForm, StripeConfigurationForm


class DashboardContextMixin(LoginRequiredMixin):
    login_url = "/login/"

    def get_companies(self):
        user = self.request.user
        return (
            Company.objects.filter(is_active=True, owner=user)
            | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
        ).distinct()

    def get_cards(self):
        return visible_profiles_queryset(self.request.user)

    def get_business_cards(self):
        return visible_business_cards_queryset(self.request.user)


class PlatformUserAccessMixin(DashboardContextMixin):
    access_denied_redirect = "dashboard-home"

    def dispatch(self, request, *args, **kwargs):
        ensure_default_permissions()
        if request.user.is_superuser or user_has_access_permission(request.user, PERM_MANAGE_PLATFORM_USERS):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "No tienes permisos para administrar usuarios.")
        return redirect(self.access_denied_redirect)


class StripeConfigurationAccessMixin(DashboardContextMixin):
    access_denied_redirect = "dashboard-home"

    def dispatch(self, request, *args, **kwargs):
        ensure_default_permissions()
        if request.user.is_superuser or user_has_access_permission(request.user, PERM_MANAGE_STRIPE_CONFIGURATION):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "No tienes permisos para configurar Stripe.")
        return redirect(self.access_denied_redirect)


def company_for_platform_user(user):
    owned_company = user.owned_companies.filter(is_active=True).order_by("name").first()
    if owned_company:
        return owned_company
    membership = user.company_memberships.filter(is_active=True, company__is_active=True).select_related("company").order_by("company__name").first()
    return membership.company if membership else None


def attach_platform_user_summary(user):
    company = company_for_platform_user(user)
    subscription = company.subscriptions.order_by("-updated_at").first() if company else None
    user.platform_company_name = company.name if company else "Sin empresa"
    user.platform_membership = subscription.plan.title() if subscription else "Sin membresia"
    return user


class DashboardUsersView(PlatformUserAccessMixin, TemplateView):
    template_name = "dashboard/users/list.html"
    paginate_by = 15

    def get_queryset(self):
        queryset = Profile.objects.all().order_by("-created_at").prefetch_related(
            "owned_companies__subscriptions",
            "company_memberships__company__subscriptions",
        )
        query = (self.request.GET.get("q") or "").strip()
        account_type = self.request.GET.get("type") or ""
        status = self.request.GET.get("status") or ""
        plan = self.request.GET.get("plan") or ""

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(owned_companies__name__icontains=query)
                | Q(company_memberships__company__name__icontains=query)
            )
        if account_type:
            queryset = queryset.filter(registration_intent=account_type)
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)
        if plan:
            queryset = queryset.filter(
                Q(owned_companies__subscriptions__plan=plan)
                | Q(company_memberships__company__subscriptions__plan=plan)
            )
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        page_obj.object_list = [attach_platform_user_summary(user) for user in page_obj.object_list]
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context.update({
            "page_obj": page_obj,
            "users": page_obj.object_list,
            "query": self.request.GET.get("q", ""),
            "account_type": self.request.GET.get("type", ""),
            "status": self.request.GET.get("status", ""),
            "plan": self.request.GET.get("plan", ""),
            "querystring": query_params.urlencode(),
            "type_choices": Profile.INTENT_CHOICES,
            "plan_choices": AccountPlanForm.PLAN_CHOICES,
        })
        return context


class DashboardUserCreateView(PlatformUserAccessMixin, CreateView):
    model = Profile
    form_class = PlatformUserForm
    template_name = "dashboard/users/form.html"
    success_url = reverse_lazy("dashboard-users")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["creating"] = True
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class DashboardUserUpdateView(PlatformUserAccessMixin, UpdateView):
    model = Profile
    form_class = PlatformUserForm
    template_name = "dashboard/users/form.html"
    success_url = reverse_lazy("dashboard-users")

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)


class DashboardUserDeactivateView(PlatformUserAccessMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(Profile, pk=pk)
        if user == request.user:
            messages.error(request, "No puedes desactivar tu propia cuenta desde este panel.")
            return redirect("dashboard-users")
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        messages.success(request, "Usuario desactivado.")
        return redirect("dashboard-users")


class DashboardStripeConfigurationView(StripeConfigurationAccessMixin, TemplateView):
    template_name = "dashboard/billing/stripe_configuration.html"

    def get_configuration(self):
        mode = self.request.POST.get("mode") or self.request.GET.get("mode") or StripeConfiguration.MODE_TEST
        return StripeConfiguration.objects.filter(mode=mode).first() or StripeConfiguration(mode=mode)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuration = kwargs.get("configuration") or self.get_configuration()
        context.update({
            "form": kwargs.get("form") or StripeConfigurationForm(instance=configuration),
            "configuration": configuration,
            "configurations": StripeConfiguration.objects.all(),
            "webhook_url": self.request.build_absolute_uri("/api/v1/stripe/webhook/"),
        })
        return context

    def post(self, request, *args, **kwargs):
        configuration = self.get_configuration()
        form = StripeConfigurationForm(request.POST, instance=configuration)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, configuration=configuration))
        saved = form.save()
        if saved.is_active:
            StripeConfiguration.objects.exclude(pk=saved.pk).update(is_active=False)
        messages.success(request, "Configuracion de Stripe guardada.")
        return redirect(f"{reverse_lazy('dashboard-stripe-configuration')}?mode={saved.mode}")


class DashboardSettingsView(DashboardContextMixin, UpdateView):
    form_class = AccountSettingsForm
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("dashboard-settings")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("new_password1"):
            update_session_auth_hash(self.request, self.object)
            messages.success(self.request, "Tu informacion personal y contrasena fueron actualizadas.")
        else:
            messages.success(self.request, "Tu informacion personal fue actualizada.")
        return response


class DashboardPlanView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/plan.html"

    plan_cards = [
        {
            "key": AccountPlanForm.PLAN_STARTER,
            "name": "Inicial",
            "price": "Gratis",
            "description": "Para validar una presencia digital sencilla.",
            "features": ["1 perfil digital", "QR publico", "Book basico"],
        },
        {
            "key": AccountPlanForm.PLAN_BUSINESS,
            "name": "Negocio",
            "price": "US$12/mes",
            "description": "Para empresas que necesitan tarjetas, website y estadisticas.",
            "features": ["Perfiles de negocio", "Presentaciones comerciales", "Website Builder"],
        },
        {
            "key": AccountPlanForm.PLAN_TEAM,
            "name": "Equipo",
            "price": "US$29/mes",
            "description": "Para manejar mas usuarios, empresas y operaciones.",
            "features": ["Equipo ampliado", "Accesos por rol", "Soporte prioritario"],
        },
    ]

    def get_form(self):
        return AccountPlanForm(user=self.request.user, data=self.request.POST or None)

    def get_current_subscription(self):
        companies = self.get_companies()
        return Subscription.objects.filter(company__in=companies).select_related("company").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or self.get_form()
        context.update({
            "form": form,
            "plan_cards": self.plan_cards,
            "current_subscription": self.get_current_subscription(),
        })
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        company = form.cleaned_data["company"]
        plan = form.cleaned_data["plan"]
        if plan != AccountPlanForm.PLAN_STARTER:
            try:
                session = create_subscription_checkout_session(company=company, plan=plan, request=request)
            except FinanceConfigurationError as exc:
                messages.error(request, f"No se pudo crear Checkout: {exc}")
                return redirect("dashboard-plan")
            return redirect(session.url)

        amount = Decimal(str(AccountPlanForm.PLAN_PRICES[plan]))
        Subscription.objects.update_or_create(
            stripe_subscription_id=f"manual-company-{company.id}",
            defaults={
                "company": company,
                "stripe_customer_id": f"manual-customer-{company.id}",
                "plan": plan,
                "unit_amount": amount,
                "currency": "USD",
                "status": Subscription.STATUS_ACTIVE,
                "billing_interval": Subscription.INTERVAL_MONTHLY,
            },
        )
        messages.success(request, "Tu seleccion de membresia fue guardada.")
        return redirect("dashboard-plan")


class DashboardHomeView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = self.get_companies()
        cards = self.get_cards()
        context.update({
            "companies": companies[:5],
            "cards": cards[:5],
            "business_cards": self.get_business_cards()[:5],
            "business_ai": business_assistant_context(self.request.user),
            "agent_profile": AgentProfile.objects.filter(user=self.request.user).first(),
            "company_count": companies.count(),
            "card_count": cards.count(),
            "business_card_count": self.get_business_cards().count(),
            "view_count": CardView.objects.filter(card__in=cards).count(),
            "click_count": CardClick.objects.filter(card__in=cards).count(),
        })
        return context


class DashboardCompaniesView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/companies.html"

    def get_active_company(self):
        companies = self.get_companies()
        company_id = self.request.GET.get("company") or self.request.POST.get("company")
        if company_id:
            company = companies.filter(pk=company_id).first()
            if company:
                return company
        return companies.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = self.get_companies().annotate(
            member_count=Count("members", distinct=True),
            card_count=Count("cards", distinct=True),
            efficient_total=Count("ratings", distinct=True),
        )
        active_company = self.get_active_company()
        posts = BusinessPost.objects.none()
        suggested = Company.objects.none()
        pending_alliances = CompanyAlliance.objects.none()
        accepted_alliances = CompanyAlliance.objects.none()
        post_form = kwargs.get("post_form") or BusinessPostForm(user=self.request.user, initial={"company": active_company})

        if active_company:
            posts = BusinessPost.objects.filter(company=active_company, is_active=True).annotate(
                excellent_count=Count("excellents", distinct=True)
            ).select_related("company")
            filters = Q()
            if active_company.category:
                filters |= Q(category__iexact=active_company.category)
            if active_company.city:
                filters |= Q(city__iexact=active_company.city)
            if active_company.region:
                filters |= Q(region__iexact=active_company.region)
            if active_company.services:
                for term in [part.strip() for part in active_company.services.replace("\n", ",").split(",") if part.strip()][:4]:
                    filters |= Q(services__icontains=term)
            suggested = Company.objects.filter(is_active=True).exclude(pk__in=self.get_companies().values("pk"))
            if filters:
                suggested = suggested.filter(filters)
            suggested = suggested.annotate(efficient_total=Count("ratings", distinct=True)).order_by("-efficient_total", "name")[:5]
            pending_alliances = CompanyAlliance.objects.filter(receiver=active_company, status=CompanyAlliance.STATUS_PENDING).select_related("requester", "receiver")
            accepted_alliances = (
                CompanyAlliance.objects.filter(status=CompanyAlliance.STATUS_ACCEPTED)
                .filter(Q(requester=active_company) | Q(receiver=active_company))
                .select_related("requester", "receiver")
            )

        stats = {
            "posts": posts.count(),
            "videos": posts.filter(media_type=BusinessPost.MEDIA_VIDEO).count(),
            "images": posts.filter(media_type=BusinessPost.MEDIA_IMAGE).count(),
            "excellent": BusinessPostExcellent.objects.filter(post__in=posts).count(),
            "views": posts.aggregate(total=Sum("view_count"))["total"] or 0,
            "alliances": accepted_alliances.count(),
            "efficient": CompanyRating.objects.filter(company=active_company).count() if active_company else 0,
        }

        context.update({
            "companies": companies,
            "active_company": active_company,
            "post_form": post_form,
            "posts": posts,
            "stats": stats,
            "business_ai": business_assistant_context(self.request.user, active_company) if active_company else business_assistant_context(self.request.user),
            "suggested_companies": suggested,
            "pending_alliances": pending_alliances,
            "accepted_alliances": accepted_alliances,
            "featured_companies": Company.objects.filter(is_active=True).annotate(efficient_total=Count("ratings", distinct=True)).order_by("-efficient_total", "name")[:4],
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "create_post":
            form = BusinessPostForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                company = form.cleaned_data["company"]
                if not can_manage_company(request.user, company):
                    messages.error(request, "No tienes permiso para publicar por esta empresa.")
                else:
                    form.save()
                    messages.success(request, "Publicacion empresarial creada.")
                    return redirect(f"{reverse_lazy('dashboard-companies')}?company={company.id}")
            return self.render_to_response(self.get_context_data(post_form=form))

        company = self.get_active_company()
        if not company:
            messages.error(request, "Selecciona una empresa.")
            return redirect("dashboard-companies")

        if action == "excellent":
            post = get_object_or_404(BusinessPost, pk=request.POST.get("post_id"), is_active=True)
            if not can_access_company(request.user, post.company):
                messages.error(request, "No puedes reaccionar a esta publicacion.")
            else:
                BusinessPostExcellent.objects.get_or_create(post=post, user=request.user)
                messages.success(request, "Marcado como Excelente.")
        elif action == "efficient":
            _, created = CompanyRating.objects.get_or_create(company=company, user=request.user, defaults={"stars": 1})
            messages.success(request, "Marcado como Eficiente." if created else "Ya marcaste esta empresa como Eficiente.")
        elif action == "request_alliance":
            receiver = get_object_or_404(Company, pk=request.POST.get("receiver_id"), is_active=True)
            if not can_manage_company(request.user, company):
                messages.error(request, "No puedes solicitar alianzas para esta empresa.")
            elif receiver == company:
                messages.error(request, "La empresa no puede aliarse consigo misma.")
            else:
                CompanyAlliance.objects.get_or_create(requester=company, receiver=receiver, defaults={"requested_by": request.user})
                messages.success(request, "Solicitud de alianza enviada.")
        elif action in {"accept_alliance", "reject_alliance"}:
            alliance = get_object_or_404(CompanyAlliance, pk=request.POST.get("alliance_id"))
            if not can_manage_company(request.user, alliance.receiver):
                messages.error(request, "No puedes decidir esta alianza.")
            else:
                alliance.status = CompanyAlliance.STATUS_ACCEPTED if action == "accept_alliance" else CompanyAlliance.STATUS_REJECTED
                alliance.save(update_fields=["status", "updated_at"])
                messages.success(request, "Alianza actualizada.")
        return redirect(f"{reverse_lazy('dashboard-companies')}?company={company.id}")


class CompanyCreateView(DashboardContextMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = "dashboard/company_form.html"
    success_url = reverse_lazy("dashboard-companies")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        CompanyMember.objects.get_or_create(
            company=self.object,
            user=self.request.user,
            defaults={"role": CompanyMember.ROLE_OWNER},
        )
        messages.success(self.request, "Empresa creada correctamente.")
        return response


class CompanyUpdateView(DashboardContextMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "dashboard/company_form.html"
    success_url = reverse_lazy("dashboard-companies")

    def get_queryset(self):
        return self.get_companies()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_manage_company(request.user, self.object):
            messages.error(request, "No tienes permiso para editar esta empresa.")
            return redirect("dashboard-companies")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Empresa actualizada correctamente.")
        return super().form_valid(form)


class CompanyDeleteView(DashboardContextMixin, View):
    def post(self, request, pk):
        company = get_object_or_404(self.get_companies(), pk=pk)
        if not can_manage_company(request.user, company):
            messages.error(request, "No tienes permiso para eliminar esta empresa.")
            return redirect("dashboard-companies")
        company.is_active = False
        company.save(update_fields=["is_active", "updated_at"])
        messages.success(request, "Empresa eliminada correctamente.")
        return redirect("dashboard-companies")


class DashboardCardsView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/cards.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_count"] = self.get_companies().count()
        context["cards"] = self.get_cards()
        return context


class DashboardBusinessCardsView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/business_cards.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_count"] = self.get_companies().count()
        context["business_cards"] = self.get_business_cards()
        return context


class DashboardBookView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/book.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_company = get_company_for_user(self.request.user, self.request.GET.get("company"))
        context["book_items"] = SavedBusiness.objects.filter(user=self.request.user).select_related(
            "company",
            "digital_card__company",
            "digital_card__user",
            "business_card__profile__company",
            "business_card__profile__user",
        )
        context["book_count"] = context["book_items"].count()
        context["active_company"] = active_company
        context["companies"] = self.get_companies()
        context["hiring_candidates"] = recommended_job_cards(active_company, limit=5) if active_company else []
        context["saved_candidates"] = (
            SavedJobCard.objects.filter(company=active_company).select_related("job_card__user", "job_card__specialty", "company")
            if active_company else SavedJobCard.objects.none()
        )
        return context


class BookDeleteView(DashboardContextMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(SavedBusiness, pk=pk, user=request.user)
        item.delete()
        messages.success(request, "Negocio eliminado de Book.")
        return redirect("dashboard-book")


class CardCreateView(DashboardContextMixin, CreateView):
    model = DigitalCard
    form_class = DigitalCardForm
    template_name = "dashboard/card_form.html"
    success_url = reverse_lazy("dashboard-cards")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        sale = record_agent_card_sale(user=self.request.user, digital_card=self.object)
        if sale:
            messages.success(self.request, "Perfil creado y comision de agente registrada.")
        else:
            messages.success(self.request, "Tarjeta creada correctamente.")
        return response


class CardUpdateView(DashboardContextMixin, UpdateView):
    model = DigitalCard
    form_class = DigitalCardForm
    template_name = "dashboard/card_form.html"
    success_url = reverse_lazy("dashboard-cards")

    def get_queryset(self):
        return self.get_cards()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_manage_business_profile(request.user, self.object):
            messages.error(request, "No tienes permiso para editar esta tarjeta.")
            return redirect("dashboard-cards")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Tarjeta actualizada correctamente.")
        return super().form_valid(form)


class CardDeleteView(DashboardContextMixin, View):
    def post(self, request, pk):
        card = get_object_or_404(self.get_cards(), pk=pk)
        if not can_manage_business_profile(request.user, card):
            messages.error(request, "No tienes permiso para eliminar esta tarjeta.")
            return redirect("dashboard-cards")
        card.is_active = False
        card.save(update_fields=["is_active", "updated_at"])
        messages.success(request, "Tarjeta eliminada correctamente.")
        return redirect("dashboard-cards")


class BusinessCardCreateView(DashboardContextMixin, CreateView):
    model = BusinessCard
    form_class = BusinessCardForm
    template_name = "dashboard/business_card_form.html"
    success_url = reverse_lazy("dashboard-business-cards")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        sale = record_agent_card_sale(user=self.request.user, business_card=self.object)
        if sale:
            messages.success(self.request, "Tarjeta de presentacion creada y comision de agente registrada.")
        else:
            messages.success(self.request, "Tarjeta de presentacion creada correctamente.")
        return response


class BusinessCardUpdateView(DashboardContextMixin, UpdateView):
    model = BusinessCard
    form_class = BusinessCardForm
    template_name = "dashboard/business_card_form.html"
    success_url = reverse_lazy("dashboard-business-cards")

    def get_queryset(self):
        return self.get_business_cards()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_use_profile_for_business_card(request.user, self.object.profile):
            messages.error(request, "No tienes permiso para editar esta tarjeta de presentacion.")
            return redirect("dashboard-business-cards")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Tarjeta de presentacion actualizada correctamente.")
        return super().form_valid(form)


class BusinessCardDeleteView(DashboardContextMixin, View):
    def post(self, request, pk):
        business_card = get_object_or_404(self.get_business_cards(), pk=pk)
        if not can_use_profile_for_business_card(request.user, business_card.profile):
            messages.error(request, "No tienes permiso para eliminar esta tarjeta de presentacion.")
            return redirect("dashboard-business-cards")
        business_card.is_active = False
        business_card.save(update_fields=["is_active", "updated_at"])
        messages.success(request, "Tarjeta de presentacion eliminada correctamente.")
        return redirect("dashboard-business-cards")


class DashboardAnalyticsView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cards = self.get_cards()
        click_labels = {
            "contact_cta_click": "Boton de contacto",
            "contact_reveal": "Informacion revelada",
            "phone_click": "Llamadas",
            "whatsapp_click": "WhatsApp",
            "email_click": "Email",
            "website_click": "Website",
            "quote_request": "Cotizaciones",
            "appointment_request": "Citas",
            "directions_click": "Direcciones",
            "message_click": "Mensajes",
            "social_click": "Redes sociales",
            "phone": "Llamadas legacy",
            "email": "Email legacy",
            "website": "Website legacy",
            "whatsapp": "WhatsApp legacy",
            "social": "Redes legacy",
        }
        click_rows = CardClick.objects.filter(card__in=cards).values("click_type").annotate(total=Count("id")).order_by("-total")
        context.update({
            "cards": cards.annotate(view_total=Count("views", distinct=True), click_total=Count("clicks", distinct=True)),
            "total_views": CardView.objects.filter(card__in=cards).count(),
            "total_clicks": CardClick.objects.filter(card__in=cards).count(),
            "click_breakdown": [
                {
                    "type": row["click_type"],
                    "label": click_labels.get(row["click_type"], row["click_type"].replace("_", " ").title()),
                    "total": row["total"],
                }
                for row in click_rows
            ],
        })
        return context
