from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.views.generic import TemplateView, View
from rest_framework import generics, permissions, status
from rest_framework.views import APIView

from accesscontrol.services import PERM_MANAGE_WEBSITE_BUILDER
from ai_agents.models import AIAgent
from ai_agents.services import public_agent_suggested_questions
from cardbookweb.responses import error_response, success_response
from cardbookweb.social import social_image_context
from cards.models import BusinessCard
from companies.models import Company
from companies.permissions import can_access_company
from forms_builder.models import FormDefinition
from .forms import BlockDashboardForm, ComponentDashboardForm, PageDashboardForm, SectionDashboardForm
from .models import (
    Block,
    BlockTranslation,
    Component,
    ComponentTranslation,
    Layout,
    Page,
    PageTranslation,
    Section,
    SectionTranslation,
    Theme,
    Website,
    WebsiteVisit,
)
from .serializers import (
    ALLOWED_FONTS,
    BlockSerializer,
    BlockTranslationSerializer,
    ComponentSerializer,
    ComponentTranslationSerializer,
    LayoutSerializer,
    PageSerializer,
    PageTranslationSerializer,
    PublicWebsiteSerializer,
    SectionSerializer,
    SectionTranslationSerializer,
    ThemeSerializer,
    WebsiteSerializer,
    validate_hex_color,
)
from .services import (
    can_manage_website_builder,
    can_publish_website_builder,
    create_starter_website,
    duplicate_block,
    duplicate_component,
    duplicate_page,
    duplicate_section,
    get_default_theme,
    website_public_url,
    website_publish_status,
)


class OwnedWebsiteQuerysetMixin:
    serializer_class = None

    def companies(self):
        user = self.request.user
        return (
            Company.objects.filter(is_active=True, owner=user)
            | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
        ).distinct()

    def managed_companies(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Company.objects.none()
        return Company.objects.filter(is_active=True).filter(
            Q(owner=user)
            | Q(members__user=user, members__is_active=True, members__role__in=["owner", "admin"])
            | Q(access_grants__user=user, access_grants__is_active=True, access_grants__role__permissions__code=PERM_MANAGE_WEBSITE_BUILDER)
            | Q(access_grants__user=user, access_grants__is_active=True, access_grants__group__permissions__code=PERM_MANAGE_WEBSITE_BUILDER)
            | Q(access_grants__user=user, access_grants__is_active=True, access_grants__group__roles__permissions__code=PERM_MANAGE_WEBSITE_BUILDER)
        ).distinct()

    def editable_queryset(self, queryset):
        return queryset.filter(**self.editable_filter())

    def editable_filter(self):
        return {}

    def perform_destroy(self, instance):
        if hasattr(instance, "is_active"):
            instance.is_active = False
            update_fields = ["is_active"]
            if hasattr(instance, "is_published"):
                instance.is_published = False
                update_fields.append("is_published")
            if hasattr(instance, "updated_at"):
                update_fields.append("updated_at")
            instance.save(update_fields=update_fields)
        elif hasattr(instance, "is_published"):
            instance.is_published = False
            instance.save(update_fields=["is_published", "updated_at"])
        else:
            super().perform_destroy(instance)


class WebsiteListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        return Website.objects.filter(company__in=self.managed_companies(), is_active=True).select_related("company", "theme")


class WebsiteDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        return Website.objects.filter(company__in=self.managed_companies(), is_active=True).select_related("company", "theme")


class PageListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(website__company__in=self.managed_companies(), website__is_active=True, is_active=True).select_related("website")


class PageDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(website__company__in=self.managed_companies(), website__is_active=True, is_active=True).select_related("website")


class LayoutListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = LayoutSerializer

    def get_queryset(self):
        return Layout.objects.filter(page__website__company__in=self.managed_companies(), page__website__is_active=True, page__is_active=True, is_active=True).select_related("page__website")


class LayoutDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LayoutSerializer

    def get_queryset(self):
        return Layout.objects.filter(page__website__company__in=self.managed_companies(), page__website__is_active=True, page__is_active=True, is_active=True).select_related("page__website")


class SectionListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SectionSerializer

    def get_queryset(self):
        return Section.objects.filter(layout__page__website__company__in=self.managed_companies(), layout__is_active=True, layout__page__is_active=True, layout__page__website__is_active=True, is_active=True).select_related("layout__page__website")


class SectionDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SectionSerializer

    def get_queryset(self):
        return Section.objects.filter(layout__page__website__company__in=self.managed_companies(), layout__is_active=True, layout__page__is_active=True, layout__page__website__is_active=True, is_active=True).select_related("layout__page__website")


class ComponentListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ComponentSerializer

    def get_queryset(self):
        return Component.objects.filter(section__layout__page__website__company__in=self.managed_companies(), section__is_active=True, section__layout__is_active=True, section__layout__page__is_active=True, section__layout__page__website__is_active=True, is_active=True).select_related("section__layout__page__website")


class ComponentDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ComponentSerializer

    def get_queryset(self):
        return Component.objects.filter(section__layout__page__website__company__in=self.managed_companies(), section__is_active=True, section__layout__is_active=True, section__layout__page__is_active=True, section__layout__page__website__is_active=True, is_active=True).select_related("section__layout__page__website")


class BlockListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = BlockSerializer

    def get_queryset(self):
        return Block.objects.filter(component__section__layout__page__website__company__in=self.managed_companies(), component__is_active=True, component__section__is_active=True, component__section__layout__is_active=True, component__section__layout__page__is_active=True, component__section__layout__page__website__is_active=True, is_active=True).select_related(
            "component__section__layout__page__website"
        )


class BlockDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlockSerializer

    def get_queryset(self):
        return Block.objects.filter(component__section__layout__page__website__company__in=self.managed_companies(), component__is_active=True, component__section__is_active=True, component__section__layout__is_active=True, component__section__layout__page__is_active=True, component__section__layout__page__website__is_active=True, is_active=True).select_related(
            "component__section__layout__page__website"
        )


class PageTranslationListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = PageTranslationSerializer

    def get_queryset(self):
        return PageTranslation.objects.filter(page__website__company__in=self.managed_companies(), page__is_active=True, page__website__is_active=True).select_related("page__website")


class PageTranslationDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PageTranslationSerializer

    def get_queryset(self):
        return PageTranslation.objects.filter(page__website__company__in=self.managed_companies(), page__is_active=True, page__website__is_active=True).select_related("page__website")


class SectionTranslationListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SectionTranslationSerializer

    def get_queryset(self):
        return SectionTranslation.objects.filter(section__layout__page__website__company__in=self.managed_companies(), section__is_active=True, section__layout__page__website__is_active=True).select_related(
            "section__layout__page__website"
        )


class SectionTranslationDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SectionTranslationSerializer

    def get_queryset(self):
        return SectionTranslation.objects.filter(section__layout__page__website__company__in=self.managed_companies(), section__is_active=True, section__layout__page__website__is_active=True).select_related(
            "section__layout__page__website"
        )


class ComponentTranslationListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ComponentTranslationSerializer

    def get_queryset(self):
        return ComponentTranslation.objects.filter(component__section__layout__page__website__company__in=self.managed_companies(), component__is_active=True, component__section__layout__page__website__is_active=True).select_related(
            "component__section__layout__page__website"
        )


class ComponentTranslationDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ComponentTranslationSerializer

    def get_queryset(self):
        return ComponentTranslation.objects.filter(component__section__layout__page__website__company__in=self.managed_companies(), component__is_active=True, component__section__layout__page__website__is_active=True).select_related(
            "component__section__layout__page__website"
        )


class BlockTranslationListCreateAPIView(OwnedWebsiteQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = BlockTranslationSerializer

    def get_queryset(self):
        return BlockTranslation.objects.filter(block__component__section__layout__page__website__company__in=self.managed_companies(), block__is_active=True, block__component__section__layout__page__website__is_active=True).select_related(
            "block__component__section__layout__page__website"
        )


class BlockTranslationDetailAPIView(OwnedWebsiteQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlockTranslationSerializer

    def get_queryset(self):
        return BlockTranslation.objects.filter(block__component__section__layout__page__website__company__in=self.managed_companies(), block__is_active=True, block__component__section__layout__page__website__is_active=True).select_related(
            "block__component__section__layout__page__website"
        )


class ThemeListAPIView(generics.ListAPIView):
    serializer_class = ThemeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Theme.objects.filter(is_active=True)


def get_public_page(website, page_slug=None):
    queryset = website.pages.filter(is_active=True, is_published=True)
    if page_slug:
        return get_object_or_404(queryset, slug=page_slug)
    page = queryset.filter(is_homepage=True).first() or queryset.order_by("order", "id").first()
    if not page:
        raise Http404("Website page not found.")
    return page


def attach_embedded_forms(sections, company):
    sections = list(sections)
    form_sections = [section for section in sections if section.section_type in {"contact_form", "form_builder"}]
    if not form_sections:
        return sections

    form_ids = []
    for section in form_sections:
        form_id = (section.settings or {}).get("form_id")
        if not form_id:
            continue
        try:
            form_ids.append(int(form_id))
        except (TypeError, ValueError):
            continue

    forms_queryset = FormDefinition.objects.filter(company=company, is_active=True).prefetch_related("fields")
    forms_by_id = {form.id: form for form in forms_queryset.filter(id__in=form_ids)}
    fallback_form = forms_queryset.order_by("name").first()

    for section in form_sections:
        form_id = (section.settings or {}).get("form_id")
        try:
            form_id = int(form_id) if form_id else None
        except (TypeError, ValueError):
            form_id = None
        section.embedded_form = forms_by_id.get(form_id) or fallback_form
    return sections


def register_visit(request, website, page, language):
    agent = request.META.get("HTTP_USER_AGENT", "")
    device = "mobile" if "Mobile" in agent else "desktop"
    WebsiteVisit.objects.create(
        website=website,
        page=page,
        language=language,
        referrer=request.META.get("HTTP_REFERER", "")[:500],
        user_agent=agent[:1000],
        device=device,
        ip_address=request.META.get("REMOTE_ADDR"),
    )


def public_website_agent(website):
    return AIAgent.objects.filter(
        company=website.company,
        agent_type=AIAgent.TYPE_WEBSITE_ASSISTANT,
        status=AIAgent.STATUS_ACTIVE,
        show_on_website=True,
        is_active=True,
    ).select_related("company", "website").first()


def public_website_queryset():
    return Website.objects.select_related("company", "theme").filter(is_active=True, is_published=True)


def find_public_website(website_slug):
    return public_website_queryset().filter(
        Q(slug=website_slug) | Q(subdomain=website_slug) | Q(company__slug=website_slug)
    ).first()


def get_public_website_or_404(website_slug):
    website = find_public_website(website_slug)
    if not website:
        raise Http404("Website not found.")
    return website


def clean_website_subdomain(value, website):
    subdomain = slugify((value or "").strip()) or slugify(website.company.slug or website.company.name)
    reserved = set(getattr(settings, "CARDBOOK_RESERVED_SUBDOMAINS", ()))
    if subdomain in reserved:
        raise ValueError("Ese subdominio esta reservado por Cardbook.")
    exists = Website.objects.exclude(pk=website.pk).filter(
        Q(subdomain=subdomain) | Q(slug=subdomain) | Q(company__slug=subdomain)
    ).exists()
    if exists:
        raise ValueError("Ese subdominio ya esta siendo usado por otra empresa.")
    return subdomain


class PublicSiteAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, website_slug, page_slug=None):
        website = get_public_website_or_404(website_slug)
        page = get_public_page(website, page_slug)
        language = request.query_params.get("lang") or website.default_language or "es"
        register_visit(request, website, page, language)
        return success_response(
            "Website retrieved successfully.",
            PublicWebsiteSerializer(website, context={"request": request, "page": page, "language": language}).data,
        )


class PublicSiteView(TemplateView):
    template_name = "website_builder/public/page_render.html"

    def get(self, request, *args, **kwargs):
        website_slug = kwargs["website_slug"]
        self.public_website = find_public_website(website_slug)
        if not self.public_website:
            company = Company.objects.filter(slug=website_slug, is_active=True).first()
            if company:
                return redirect("public-company-detail", slug=company.slug)
            business_card = BusinessCard.objects.filter(
                is_active=True,
                profile__is_active=True,
                website__icontains=f"/site/{website_slug}/",
            ).order_by("-updated_at").first()
            if business_card:
                return redirect("public-business-card", slug=business_card.slug)
            raise Http404("Website not found.")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        website = self.public_website
        page = get_public_page(website, kwargs.get("page_slug"))
        language = self.request.GET.get("lang") or website.default_language or "es"
        register_visit(self.request, website, page, language)
        layout = getattr(page, "layout", None)
        sections = layout.sections.filter(is_active=True).prefetch_related(
            "components__blocks",
            "translations",
            "components__translations",
            "components__blocks__translations",
        ) if layout and layout.is_active else []
        context.update({
            "website": website,
            "page": page,
            "language": language,
            "menu_pages": website.pages.filter(is_active=True, is_published=True, show_in_menu=True).order_by("order", "title"),
            "sections": attach_embedded_forms(sections, website.company),
            "public_ai_agent": public_website_agent(website),
            "social_title": page.og_title or page.seo_title or website.meta_title or website.title,
            "social_description": page.seo_description or website.meta_description or website.company.description or "Website empresarial en incardbook.",
            **social_image_context(self.request, page.og_image, website.logo, website.company.logo),
        })
        context["public_ai_suggestions"] = public_agent_suggested_questions(context["public_ai_agent"])
        return context


class DashboardWebsitePreviewView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "website_builder/public/page_render.html"

    def get_company(self):
        company = get_object_or_404(Company, pk=self.kwargs["company_id"], is_active=True)
        if not can_access_company(self.request.user, company):
            raise Http404("Company not found.")
        return company

    def get_page(self, website):
        page_id = self.kwargs.get("page_id")
        queryset = website.pages.filter(is_active=True)
        if page_id:
            return get_object_or_404(queryset, pk=page_id)
        page = queryset.filter(is_homepage=True).first() or queryset.order_by("order", "id").first()
        if not page:
            raise Http404("Website page not found.")
        return page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        website = get_object_or_404(Website.objects.select_related("company", "theme"), company=company, is_active=True)
        page = self.get_page(website)
        language = self.request.GET.get("lang") or website.default_language or "es"
        layout = getattr(page, "layout", None)
        sections = layout.sections.filter(is_active=True).prefetch_related(
            "components__blocks",
            "translations",
            "components__translations",
            "components__blocks__translations",
        ) if layout and layout.is_active else []
        context.update({
            "website": website,
            "page": page,
            "language": language,
            "menu_pages": website.pages.filter(is_active=True, show_in_menu=True).order_by("order", "title"),
            "sections": attach_embedded_forms(sections, website.company),
            "public_ai_agent": public_website_agent(website),
            "social_title": page.og_title or page.seo_title or website.meta_title or website.title,
            "social_description": page.seo_description or website.meta_description or website.company.description or "Website empresarial en incardbook.",
            **social_image_context(self.request, page.og_image, website.logo, website.company.logo),
        })
        context["public_ai_suggestions"] = public_agent_suggested_questions(context["public_ai_agent"])
        return context


class DashboardWebsiteBuilderView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "website_builder/dashboard/builder.html"

    def get_company(self):
        company = get_object_or_404(Company, pk=self.kwargs["company_id"], is_active=True)
        if not can_access_company(self.request.user, company):
            raise Http404("Company not found.")
        return company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        website = Website.objects.filter(company=company, is_active=True).select_related("theme").first()
        pages = list(website.pages.filter(is_active=True).prefetch_related("layout__sections__components__blocks")) if website else []
        for page in pages:
            layout = getattr(page, "layout", None)
            page.active_sections = [section for section in layout.sections.all() if section.is_active] if layout else []
            for section in page.active_sections:
                section.active_components = [component for component in section.components.all() if component.is_active]
                for component in section.active_components:
                    component.active_blocks = [block for block in component.blocks.all() if block.is_active]
        context.update({
            "company": company,
            "website": website,
            "can_manage_website": can_manage_website_builder(self.request.user, company),
            "can_publish_website": can_publish_website_builder(self.request.user, company),
            "publish_status": website_publish_status(website),
            "public_url": website_public_url(self.request, website) if website else "",
            "public_site_base_domain": getattr(settings, "CARDBOOK_PUBLIC_SITE_BASE_DOMAIN", "incardbook.com"),
            "themes": Theme.objects.filter(is_active=True),
            "visits": WebsiteVisit.objects.filter(website=website).count() if website else 0,
            "website_ai_agent": public_website_agent(website) if website else None,
            "pages": pages,
            "page_form": kwargs.get("page_form") or PageDashboardForm(),
            "page_edit_form": kwargs.get("page_edit_form"),
            "editing_page": kwargs.get("editing_page"),
            "section_form": kwargs.get("section_form") or SectionDashboardForm(initial={"is_active": True}),
            "section_edit_form": kwargs.get("section_edit_form"),
            "editing_section": kwargs.get("editing_section"),
            "component_form": kwargs.get("component_form") or ComponentDashboardForm(initial={"is_active": True}),
            "component_edit_form": kwargs.get("component_edit_form"),
            "editing_component": kwargs.get("editing_component"),
            "block_form": kwargs.get("block_form") or BlockDashboardForm(initial={"is_active": True}),
            "block_edit_form": kwargs.get("block_edit_form"),
            "editing_block": kwargs.get("editing_block"),
        })
        return context

    def post(self, request, *args, **kwargs):
        company = self.get_company()
        action = request.POST.get("action")
        publish_actions = {"publish", "unpublish"}
        if action in publish_actions and not can_publish_website_builder(request.user, company):
            messages.error(request, "No tienes permiso para publicar este sitio.")
            return redirect("dashboard-company-website", company_id=company.id)
        if action not in publish_actions and not can_manage_website_builder(request.user, company):
            messages.error(request, "No tienes permiso para editar el sitio de esta empresa.")
            return redirect("dashboard-company-website", company_id=company.id)

        website = Website.objects.filter(company=company, is_active=True).first()
        if action == "create_website":
            website = create_starter_website(company, publish=False)
            messages.success(request, "Website Builder creado con plantilla inicial.")
        elif action == "update_identity" and website:
            try:
                website.title = (request.POST.get("title") or website.title).strip()[:180]
                website.subdomain = clean_website_subdomain(request.POST.get("subdomain"), website)
                website.domain = (request.POST.get("domain") or "").strip()[:255]
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("dashboard-company-website", company_id=company.id)
            website.save(update_fields=["title", "subdomain", "domain", "updated_at"])
            messages.success(request, "Identidad publica del website actualizada.")
        elif action == "update_contact_visibility" and website:
            company.show_phone = request.POST.get("show_phone") == "on"
            company.show_whatsapp = request.POST.get("show_whatsapp") == "on"
            company.show_email = request.POST.get("show_email") == "on"
            company.show_website = request.POST.get("show_website") == "on"
            company.show_address = request.POST.get("show_address") == "on"
            company.save(update_fields=[
                "show_phone",
                "show_whatsapp",
                "show_email",
                "show_website",
                "show_address",
                "updated_at",
            ])
            messages.success(request, "Visibilidad de contacto actualizada.")
        elif action == "create_page" and website:
            form = PageDashboardForm(request.POST)
            if form.is_valid():
                page = form.save(commit=False)
                page.website = website
                page.save()
                Layout.objects.get_or_create(page=page, defaults={"layout_type": Layout.FULL_WIDTH, "name": "Layout principal"})
                messages.success(request, "Pagina creada correctamente.")
            else:
                return self.render_to_response(self.get_context_data(page_form=form))
        elif action == "update_page" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            form = PageDashboardForm(request.POST, instance=page)
            if form.is_valid():
                form.save()
                messages.success(request, "Pagina actualizada correctamente.")
            else:
                return self.render_to_response(self.get_context_data(page_edit_form=form, editing_page=page))
        elif action == "duplicate_page" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            duplicate_page(page)
            messages.success(request, "Pagina duplicada como borrador.")
        elif action == "toggle_page_publish" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            page.is_published = not page.is_published
            page.save(update_fields=["is_published", "updated_at"])
            messages.success(request, "Estado de publicacion actualizado.")
        elif action == "set_homepage" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            page.is_homepage = True
            page.is_published = True
            page.show_in_menu = True
            page.save(update_fields=["is_homepage", "is_published", "show_in_menu", "updated_at"])
            messages.success(request, "Pagina principal actualizada.")
        elif action == "archive_page" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            if page.is_homepage:
                messages.error(request, "No puedes archivar la pagina principal. Define otra homepage primero.")
            else:
                page.is_active = False
                page.is_published = False
                page.save(update_fields=["is_active", "is_published", "updated_at"])
                messages.success(request, "Pagina archivada.")
        elif action == "delete_page" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            active_pages = website.pages.filter(is_active=True)
            if active_pages.count() <= 1:
                messages.error(request, "No puedes eliminar la unica pagina activa del website.")
            else:
                page_title = page.title
                if page.is_homepage:
                    replacement = active_pages.exclude(pk=page.pk).order_by("order", "id").first()
                    replacement.is_homepage = True
                    replacement.is_published = True
                    replacement.show_in_menu = True
                    replacement.save(update_fields=["is_homepage", "is_published", "show_in_menu", "updated_at"])
                page.delete()
                messages.success(request, f"Pagina {page_title} eliminada.")
        elif action == "create_section" and website:
            page = get_object_or_404(Page, pk=request.POST.get("page_id"), website=website, is_active=True)
            layout, _ = Layout.objects.get_or_create(page=page, defaults={"layout_type": Layout.FULL_WIDTH, "name": "Layout principal"})
            form = SectionDashboardForm(request.POST)
            if form.is_valid():
                section = form.save(commit=False)
                section.layout = layout
                section.save()
                messages.success(request, "Seccion creada correctamente.")
            else:
                return self.render_to_response(self.get_context_data(section_form=form))
        elif action == "update_section" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            form = SectionDashboardForm(request.POST, instance=section)
            if form.is_valid():
                form.save()
                messages.success(request, "Seccion actualizada correctamente.")
            else:
                return self.render_to_response(self.get_context_data(section_edit_form=form, editing_section=section))
        elif action == "create_hero_slide" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website, section_type="hero")
            image = request.FILES.get("image")
            if not image:
                messages.error(request, "Selecciona una imagen para el carrusel.")
                return redirect("dashboard-company-website", company_id=company.id)
            component, _ = Component.objects.get_or_create(
                section=section,
                component_type="custom_component",
                name="Carrusel del header",
                defaults={"title": "Carrusel del header", "order": 0, "is_active": True},
            )
            Block.objects.create(
                component=component,
                block_type="image",
                key=request.POST.get("key") or f"slide-{component.blocks.count() + 1}",
                image=image,
                button_text=request.POST.get("button_text", ""),
                text=request.POST.get("text", ""),
                value=request.POST.get("value", ""),
                order=component.blocks.count() + 1,
                is_active=True,
            )
            messages.success(request, "Imagen agregada al carrusel del header.")
        elif action == "duplicate_section" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            duplicate_section(section)
            messages.success(request, "Seccion duplicada como borrador.")
        elif action == "toggle_section" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            section.is_active = not section.is_active
            section.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Estado de seccion actualizado.")
        elif action == "archive_section" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            section.is_active = False
            section.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Seccion archivada.")
        elif action in {"move_section_up", "move_section_down"} and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            if action == "move_section_up":
                section.order = max(section.order - 1, 0)
            else:
                section.order = section.order + 1
            section.save(update_fields=["order", "updated_at"])
            messages.success(request, "Orden de seccion actualizado.")
        elif action == "create_component" and website:
            section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website=website)
            form = ComponentDashboardForm(request.POST)
            if form.is_valid():
                component = form.save(commit=False)
                component.section = section
                component.save()
                messages.success(request, "Componente creado correctamente.")
            else:
                return self.render_to_response(self.get_context_data(component_form=form))
        elif action == "update_component" and website:
            component = get_object_or_404(Component, pk=request.POST.get("component_id"), section__layout__page__website=website)
            form = ComponentDashboardForm(request.POST, instance=component)
            if form.is_valid():
                form.save()
                messages.success(request, "Componente actualizado correctamente.")
            else:
                return self.render_to_response(self.get_context_data(component_edit_form=form, editing_component=component))
        elif action == "duplicate_component" and website:
            component = get_object_or_404(Component, pk=request.POST.get("component_id"), section__layout__page__website=website)
            duplicate_component(component)
            messages.success(request, "Componente duplicado como borrador.")
        elif action == "toggle_component" and website:
            component = get_object_or_404(Component, pk=request.POST.get("component_id"), section__layout__page__website=website)
            component.is_active = not component.is_active
            component.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Estado de componente actualizado.")
        elif action in {"move_component_up", "move_component_down"} and website:
            component = get_object_or_404(Component, pk=request.POST.get("component_id"), section__layout__page__website=website)
            component.order = max(component.order - 1, 0) if action == "move_component_up" else component.order + 1
            component.save(update_fields=["order", "updated_at"])
            messages.success(request, "Orden de componente actualizado.")
        elif action == "create_block" and website:
            component = get_object_or_404(Component, pk=request.POST.get("component_id"), section__layout__page__website=website)
            form = BlockDashboardForm(request.POST, request.FILES)
            if form.is_valid():
                block = form.save(commit=False)
                block.component = component
                block.save()
                messages.success(request, "Bloque creado correctamente.")
            else:
                return self.render_to_response(self.get_context_data(block_form=form))
        elif action == "update_block" and website:
            block = get_object_or_404(Block, pk=request.POST.get("block_id"), component__section__layout__page__website=website)
            form = BlockDashboardForm(request.POST, request.FILES, instance=block)
            if form.is_valid():
                form.save()
                messages.success(request, "Bloque actualizado correctamente.")
            else:
                return self.render_to_response(self.get_context_data(block_edit_form=form, editing_block=block))
        elif action == "duplicate_block" and website:
            block = get_object_or_404(Block, pk=request.POST.get("block_id"), component__section__layout__page__website=website)
            duplicate_block(block)
            messages.success(request, "Bloque duplicado como borrador.")
        elif action == "toggle_block" and website:
            block = get_object_or_404(Block, pk=request.POST.get("block_id"), component__section__layout__page__website=website)
            block.is_active = not block.is_active
            block.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Estado de bloque actualizado.")
        elif action in {"move_block_up", "move_block_down"} and website:
            block = get_object_or_404(Block, pk=request.POST.get("block_id"), component__section__layout__page__website=website)
            block.order = max(block.order - 1, 0) if action == "move_block_up" else block.order + 1
            block.save(update_fields=["order", "updated_at"])
            messages.success(request, "Orden de bloque actualizado.")
        elif action == "publish" and website:
            if not can_publish_website_builder(request.user, company):
                messages.error(request, "No tienes permiso para publicar este sitio.")
            else:
                status_info = website_publish_status(website)
                if not status_info["can_publish"]:
                    messages.error(request, "Antes de publicar: " + " ".join(status_info["issues"]))
                else:
                    website.is_published = True
                    website.save(update_fields=["is_published", "updated_at"])
                    messages.success(request, "Sitio publicado.")
        elif action == "unpublish" and website:
            if not can_publish_website_builder(request.user, company):
                messages.error(request, "No tienes permiso para despublicar este sitio.")
            else:
                website.is_published = False
                website.save(update_fields=["is_published", "updated_at"])
                messages.success(request, "Sitio despublicado.")
        elif action == "update_theme" and website:
            theme = Theme.objects.filter(pk=request.POST.get("theme"), is_active=True).first()
            if theme:
                website.theme = theme
            try:
                primary_color = request.POST.get("primary_color") or website.primary_color
                secondary_color = request.POST.get("secondary_color") or website.secondary_color
                accent_color = request.POST.get("accent_color") or website.accent_color
                validate_hex_color(primary_color, "primary_color")
                validate_hex_color(secondary_color, "secondary_color")
                validate_hex_color(accent_color, "accent_color")
            except Exception:
                messages.error(request, "Usa colores validos en formato hexadecimal.")
                return redirect("dashboard-company-website", company_id=company.id)
            font_family = request.POST.get("font_family") or website.font_family
            if font_family not in ALLOWED_FONTS:
                messages.error(request, "La tipografia seleccionada no esta disponible.")
                return redirect("dashboard-company-website", company_id=company.id)
            website.primary_color = primary_color
            website.secondary_color = secondary_color
            website.accent_color = accent_color
            website.font_family = font_family
            if request.POST.get("update_structure") == "1":
                website.show_header = request.POST.get("show_header") == "on"
                website.show_nav = request.POST.get("show_nav") == "on"
            website.save()
            messages.success(request, "Estilo del sitio actualizado.")
        return redirect("dashboard-company-website", company_id=company.id)
