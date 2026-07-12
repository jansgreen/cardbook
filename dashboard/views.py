from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView, View

from analytics.models import CardClick, CardView
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
from referrals.services import record_agent_card_sale
from .forms import BusinessCardForm, BusinessPostForm, CompanyForm, DigitalCardForm


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
        context["cards"] = self.get_cards()
        return context


class DashboardBusinessCardsView(DashboardContextMixin, TemplateView):
    template_name = "dashboard/business_cards.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context.update({
            "cards": cards.annotate(view_total=Count("views", distinct=True), click_total=Count("clicks", distinct=True)),
            "total_views": CardView.objects.filter(card__in=cards).count(),
            "total_clicks": CardClick.objects.filter(card__in=cards).count(),
        })
        return context
