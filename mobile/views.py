from django.db.models import Count, Q
from django.urls import reverse
from rest_framework import permissions
from rest_framework.views import APIView

from accounts.serializers import ProfileSerializer
from alliances.models import CompanyAlliance
from ai_agents.api_serializers import AIAgentSerializer
from ai_agents.models import AIAgent
from ai_agents.services import agent_analytics, public_agent_suggested_questions, sync_agents_for_user
from book.models import SavedBusiness
from book.serializers import SavedBusinessSerializer
from business_feed.models import BusinessPost
from business_feed.serializers import BusinessPostSerializer
from cards.serializers import BusinessCardSerializer, DigitalCardSerializer
from cards.services import profile_creation_companies, visible_business_cards_queryset, visible_profiles_queryset
from cardbookweb.responses import StandardPagination, success_response
from companies.models import Company
from companies.permissions import can_manage_company
from companies.serializers import CompanySerializer
from forms_builder.models import FormDefinition
from jobcards.models import SavedJobCard, WhiteCardJob
from jobcards.serializers import SavedJobCardSerializer, WhiteCardJobSerializer
from jobcards.services import get_company_for_user, recommended_job_cards, user_active_job_card
from websitebuilder.models import Website
from websitebuilder.serializers import WebsiteSerializer
from websitebuilder.services import can_manage_website_builder, can_publish_website_builder, website_public_url
from dashboard.access_policy import (
    SECTION_ACCESS,
    SECTION_AI_AGENTS,
    SECTION_BOOK,
    SECTION_BUSINESS_CARDS,
    SECTION_CARDS,
    SECTION_COMPANIES,
    SECTION_FINANCE,
    SECTION_FORMS,
    SECTION_NOTIFICATIONS,
    SECTION_REFERRALS,
    SECTION_WEBSITE,
    SECTION_WHITE_CARD_JOB,
    allowed_dashboard_sections,
    dashboard_menu_for_user,
    dashboard_user_type,
)


MOBILE_SECTION_ENDPOINTS = {
    "home": "mobile-dashboard",
    SECTION_COMPANIES: "mobile-companies",
    SECTION_CARDS: "mobile-cards",
    SECTION_BUSINESS_CARDS: "mobile-cards",
    SECTION_BOOK: "mobile-book",
    SECTION_WHITE_CARD_JOB: "mobile-jobs",
    SECTION_WEBSITE: "mobile-websites",
    SECTION_FORMS: "mobile-forms",
    SECTION_AI_AGENTS: "mobile-ai-agents",
}


def absolute_url(request, path_or_url):
    if not path_or_url:
        return ""
    if str(path_or_url).startswith(("http://", "https://")):
        return str(path_or_url)
    return request.build_absolute_uri(path_or_url)


def user_companies_queryset(user):
    return profile_creation_companies(user)


def paginate_response(request, queryset, serializer_class):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def mobile_endpoints(request):
    return {
        "config": request.build_absolute_uri(reverse("mobile-config")),
        "bootstrap": request.build_absolute_uri(reverse("mobile-bootstrap")),
        "dashboard": request.build_absolute_uri(reverse("mobile-dashboard")),
        "companies": request.build_absolute_uri(reverse("mobile-companies")),
        "cards": request.build_absolute_uri(reverse("mobile-cards")),
        "book": request.build_absolute_uri(reverse("mobile-book")),
        "jobs": request.build_absolute_uri(reverse("mobile-jobs")),
        "websites": request.build_absolute_uri(reverse("mobile-websites")),
        "forms": request.build_absolute_uri(reverse("mobile-forms")),
        "ai_agents": request.build_absolute_uri(reverse("mobile-ai-agents")),
        "actions": request.build_absolute_uri(reverse("mobile-actions")),
        "push_devices": request.build_absolute_uri(reverse("push-devices")),
        "push_test": request.build_absolute_uri(reverse("push-test")),
    }


def crud_links(request):
    return {
        "companies": request.build_absolute_uri(reverse("company-list")),
        "digital_cards": request.build_absolute_uri(reverse("card-list")),
        "business_cards": request.build_absolute_uri(reverse("business-card-list")),
        "book": request.build_absolute_uri(reverse("book-list")),
        "jobcards": request.build_absolute_uri(reverse("jobcard-list")),
        "jobcard_me": request.build_absolute_uri(reverse("jobcard-me")),
        "websites": request.build_absolute_uri(reverse("api-website-list")),
    }


def mobile_navigation(request):
    payload = []
    for item in dashboard_menu_for_user(request.user):
        endpoint_name = MOBILE_SECTION_ENDPOINTS.get(item["key"])
        payload.append({
            "key": item["key"],
            "label": item["label"],
            "endpoint": request.build_absolute_uri(reverse(endpoint_name)) if endpoint_name else "",
            "web_url": request.build_absolute_uri(item["url"]),
            "available_native": bool(endpoint_name),
        })
    return payload


def mobile_capabilities(request, companies, active_company=None):
    user_type = dashboard_user_type(request.user)
    allowed_sections = allowed_dashboard_sections(request.user)
    has_companies = companies.exists()
    has_profiles = visible_profiles_queryset(request.user).exists()

    return {
        "can_create_company": user_type in {"company", "agent", "superuser"} and SECTION_COMPANIES in allowed_sections,
        "can_create_digital_card": SECTION_CARDS in allowed_sections and has_companies,
        "can_create_business_card": SECTION_BUSINESS_CARDS in allowed_sections and has_profiles,
        "can_create_white_card_job": SECTION_WHITE_CARD_JOB in allowed_sections and (
            user_type in {"job", "agent", "superuser"} or bool(user_active_job_card(request.user))
        ),
        "can_manage_active_company": can_manage_company(request.user, active_company) if active_company else False,
        "can_manage_website": SECTION_WEBSITE in allowed_sections and can_manage_website_builder(request.user, active_company) if active_company else False,
        "can_publish_website": SECTION_WEBSITE in allowed_sections and can_publish_website_builder(request.user, active_company) if active_company else False,
        "can_manage_forms": SECTION_FORMS in allowed_sections and can_manage_website_builder(request.user, active_company) if active_company else False,
        "can_manage_ai_agents": SECTION_AI_AGENTS in allowed_sections and has_companies,
        "can_use_book": SECTION_BOOK in allowed_sections,
        "can_view_notifications": SECTION_NOTIFICATIONS in allowed_sections,
        "can_view_referrals": SECTION_REFERRALS in allowed_sections,
        "can_view_finance": SECTION_FINANCE in allowed_sections,
        "can_manage_access": SECTION_ACCESS in allowed_sections,
    }


def mobile_access_payload(request, companies=None, active_company=None):
    if companies is None:
        companies = user_companies_queryset(request.user)
    if active_company is None:
        active_company = companies.first()
    menu = mobile_navigation(request)
    user_type = dashboard_user_type(request.user)
    return {
        "registration_intent": getattr(request.user, "registration_intent", ""),
        "account_type": user_type,
        "allowed_sections": sorted(allowed_dashboard_sections(request.user)),
        "menu": menu,
        "navigation": menu,
        "capabilities": mobile_capabilities(request, companies, active_company=active_company),
    }


class MobileConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = {
            "app": "cardbook",
            "api_version": "v1",
            "platforms": ["android", "ios"],
            "auth": {
                "login": request.build_absolute_uri(reverse("login")),
                "register": request.build_absolute_uri(reverse("register")),
                "refresh": request.build_absolute_uri(reverse("token-refresh")),
                "verify": request.build_absolute_uri(reverse("token-verify")),
                "me": request.build_absolute_uri(reverse("account-me")),
            },
            "mobile": {
                **mobile_endpoints(request),
            },
            "crud": crud_links(request),
            "public_base_url": request.build_absolute_uri("/"),
            "media_base_url": request.build_absolute_uri("/media/"),
            "android_version": request.build_absolute_uri(reverse("web-android-version")),
            "android_download": request.build_absolute_uri(reverse("web-android-download")),
            "push": {
                "devices": request.build_absolute_uri(reverse("push-devices")),
                "disable": request.build_absolute_uri(reverse("push-device-disable")),
                "test": request.build_absolute_uri(reverse("push-test")),
            },
            "ai_agents": {
                "list": request.build_absolute_uri(reverse("api-ai-agent-list")),
                "mobile": request.build_absolute_uri(reverse("mobile-ai-agents")),
            },
        }
        return success_response("Mobile config retrieved successfully.", data)


class MobileBootstrapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        active_company = companies.first()
        access_payload = mobile_access_payload(request, companies=companies, active_company=active_company)
        data = {
            "user": ProfileSerializer(request.user, context={"request": request}).data,
            "endpoints": mobile_endpoints(request),
            "crud": crud_links(request),
            **access_payload,
        }
        return success_response("Mobile bootstrap retrieved successfully.", data)


class MobileDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        company_ids = list(companies.values_list("id", flat=True))

        cards = visible_profiles_queryset(request.user)
        business_cards = visible_business_cards_queryset(request.user)
        posts = BusinessPost.objects.filter(is_active=True, company_id__in=company_ids).select_related("company").annotate(
            excellent_count=Count("excellents", distinct=True)
        )
        alliances = CompanyAlliance.objects.filter(Q(requester_id__in=company_ids) | Q(receiver_id__in=company_ids))
        accepted_alliances = alliances.filter(status=CompanyAlliance.STATUS_ACCEPTED)
        pending_alliances = alliances.filter(status=CompanyAlliance.STATUS_PENDING)

        suggested_companies = (
            Company.objects.filter(is_active=True)
            .exclude(id__in=company_ids)
            .annotate(efficient_total=Count("ratings", distinct=True))
            .order_by("-efficient_total", "name")[:5]
        )

        total_views = sum(card.views.count() for card in cards)
        total_clicks = sum(card.clicks.count() for card in cards)

        data = {
            "user": ProfileSerializer(request.user, context={"request": request}).data,
            **mobile_access_payload(request, companies=companies, active_company=companies.first()),
            "summary": {
                "companies": companies.count(),
                "digital_cards": cards.count(),
                "business_cards": business_cards.count(),
                "book_items": SavedBusiness.objects.filter(user=request.user).count(),
                "posts": posts.count(),
                "alliances": accepted_alliances.count(),
                "pending_alliances": pending_alliances.count(),
                "views": total_views,
                "clicks": total_clicks,
                "excellent": sum(company.efficient_count for company in companies),
                "notifications": pending_alliances.count(),
            },
            "companies": CompanySerializer(companies.annotate(efficient_total=Count("ratings", distinct=True))[:5], many=True, context={"request": request}).data,
            "digital_cards": DigitalCardSerializer(cards[:5], many=True, context={"request": request}).data,
            "business_cards": BusinessCardSerializer(business_cards[:5], many=True, context={"request": request}).data,
            "recent_posts": BusinessPostSerializer(posts[:5], many=True, context={"request": request}).data,
            "suggested_companies": CompanySerializer(suggested_companies, many=True, context={"request": request}).data,
            "quick_links": {
                "companies": request.build_absolute_uri("/api/v1/companies/"),
                "cards": request.build_absolute_uri("/api/v1/cards/"),
                "business_cards": request.build_absolute_uri("/api/v1/cards/business-cards/"),
                "posts": request.build_absolute_uri("/api/v1/posts/"),
                "alliances": request.build_absolute_uri("/api/v1/alliances/"),
                "book": request.build_absolute_uri("/api/v1/book/"),
            },
        }
        return success_response("Mobile dashboard retrieved successfully.", data)


class MobileCompaniesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user).annotate(efficient_total=Count("ratings", distinct=True)).order_by("name", "id")
        return paginate_response(request, companies, CompanySerializer)


class MobileCardsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        digital_cards = visible_profiles_queryset(request.user)
        business_cards = visible_business_cards_queryset(request.user)
        data = {
            "digital_cards": DigitalCardSerializer(digital_cards, many=True, context={"request": request}).data,
            "business_cards": BusinessCardSerializer(business_cards, many=True, context={"request": request}).data,
            "create_links": {
                "digital_card": request.build_absolute_uri(reverse("card-list")),
                "business_card": request.build_absolute_uri(reverse("business-card-list")),
            },
        }
        return success_response("Mobile cards retrieved successfully.", data)


class MobileBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_company = get_company_for_user(request.user, request.query_params.get("company"))
        business_items = SavedBusiness.objects.filter(user=request.user).select_related(
            "company",
            "digital_card__company",
            "digital_card__user",
            "business_card__profile__company",
            "business_card__profile__user",
        )
        saved_candidates = (
            SavedJobCard.objects.filter(company=active_company).select_related("company", "job_card__user", "job_card__specialty", "saved_by")
            if active_company else SavedJobCard.objects.none()
        )
        data = {
            "active_company": CompanySerializer(active_company, context={"request": request}).data if active_company else None,
            "businesses": SavedBusinessSerializer(business_items, many=True, context={"request": request}).data,
            "saved_candidates": SavedJobCardSerializer(saved_candidates, many=True, context={"request": request}).data,
            "recommendations": WhiteCardJobSerializer(recommended_job_cards(active_company, limit=8), many=True, context={"request": request}).data if active_company else [],
        }
        return success_response("Mobile book retrieved successfully.", data)


class MobileJobsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = get_company_for_user(request.user, request.query_params.get("company"))
        my_card = user_active_job_card(request.user)
        public_jobs = WhiteCardJob.objects.filter(is_active=True, is_available=True).select_related("user", "specialty")
        specialty = request.query_params.get("specialty")
        if specialty:
            public_jobs = public_jobs.filter(specialty__slug=specialty)
        data = {
            "my_card": WhiteCardJobSerializer(my_card, context={"request": request}).data if my_card else None,
            "available_jobs": WhiteCardJobSerializer(public_jobs[:30], many=True, context={"request": request}).data,
            "recommended_for_company": WhiteCardJobSerializer(recommended_job_cards(company, limit=8), many=True, context={"request": request}).data if company else [],
        }
        return success_response("Mobile jobs retrieved successfully.", data)


class MobileWebsitesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        websites = (
            Website.objects.filter(company__in=companies, is_active=True)
            .select_related("company", "theme")
            .prefetch_related("pages__layout__sections")
        )
        serialized = WebsiteSerializer(websites, many=True, context={"request": request}).data
        websites_by_id = {website.id: website for website in websites}
        enriched_websites = []
        for item in serialized:
            website = websites_by_id.get(item["id"])
            if not website:
                enriched_websites.append(item)
                continue
            pages = list(website.pages.filter(is_active=True).order_by("order", "title"))
            page_payload = []
            section_count = 0
            for page in pages:
                layout = getattr(page, "layout", None)
                page_sections = list(layout.sections.filter(is_active=True)) if layout and layout.is_active else []
                section_count += len(page_sections)
                page_payload.append({
                    "id": page.id,
                    "title": page.title,
                    "slug": page.slug,
                    "is_homepage": page.is_homepage,
                    "is_published": page.is_published,
                    "show_in_menu": page.show_in_menu,
                    "section_count": len(page_sections),
                    "public_url": website_public_url(request, website, page) if page.is_published else "",
                })
            item.update({
                "company_name": website.company.name,
                "company_id": website.company_id,
                "builder_url": request.build_absolute_uri(
                    reverse("dashboard-company-website", kwargs={"company_id": website.company_id})
                ),
                "can_manage": can_manage_website_builder(request.user, website.company),
                "can_publish": can_publish_website_builder(request.user, website.company),
                "page_count": len(pages),
                "published_page_count": sum(1 for page in pages if page.is_published),
                "section_count": section_count,
                "pages": page_payload,
            })
            enriched_websites.append(item)
        data = {
            "websites": enriched_websites,
            "create_link": request.build_absolute_uri(reverse("api-website-list")),
            "builder_home": request.build_absolute_uri("/dashboard/companies/"),
        }
        return success_response("Mobile websites retrieved successfully.", data)


class MobileFormsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        forms = (
            FormDefinition.objects.filter(company__in=companies)
            .select_related("company")
            .prefetch_related("fields", "submissions")
            .order_by("company__name", "name")
        )
        forms_payload = []
        for form_definition in forms:
            public_url = request.build_absolute_uri(
                reverse(
                    "forms-builder-public-detail",
                    kwargs={
                        "company_slug": form_definition.company.slug,
                        "form_slug": form_definition.slug,
                    },
                )
            )
            dashboard_url = request.build_absolute_uri(
                reverse(
                    "dashboard-form-builder-detail",
                    kwargs={
                        "company_id": form_definition.company_id,
                        "form_id": form_definition.id,
                    },
                )
            )
            fields = list(form_definition.fields.filter(is_active=True).order_by("order", "id"))
            forms_payload.append({
                "id": form_definition.id,
                "name": form_definition.name,
                "slug": form_definition.slug,
                "description": form_definition.description,
                "recipient_email": form_definition.recipient_email,
                "success_message": form_definition.success_message,
                "is_active": form_definition.is_active,
                "company_id": form_definition.company_id,
                "company_name": form_definition.company.name,
                "company_slug": form_definition.company.slug,
                "public_url": public_url,
                "dashboard_url": dashboard_url,
                "field_count": len(fields),
                "submission_count": form_definition.submissions.count(),
                "fields": [
                    {
                        "id": field.id,
                        "label": field.label,
                        "field_type": field.field_type,
                        "placeholder": field.placeholder,
                        "help_text": field.help_text,
                        "choices": field.choice_list(),
                        "is_required": field.is_required,
                        "order": field.order,
                    }
                    for field in fields
                ],
                "created_at": form_definition.created_at,
                "updated_at": form_definition.updated_at,
            })
        data = {
            "forms": forms_payload,
            "builder_home": request.build_absolute_uri("/dashboard/companies/"),
        }
        return success_response("Mobile forms retrieved successfully.", data)


class MobileAIAgentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = user_companies_queryset(request.user)
        sync_agents_for_user(request.user)
        agents = (
            AIAgent.objects.filter(company__in=companies, is_active=True)
            .select_related("company", "website")
            .prefetch_related("knowledge_items", "faqs", "leads", "suggestions", "conversations")
            .order_by("company__name", "agent_type", "name")
        )
        serialized = AIAgentSerializer(agents, many=True, context={"request": request}).data
        agents_by_id = {agent.id: agent for agent in agents}
        enriched_agents = []
        for item in serialized:
            agent = agents_by_id.get(item["id"])
            if not agent:
                enriched_agents.append(item)
                continue
            analytics = agent_analytics(agent)
            open_suggestions = agent.suggestions.filter(is_resolved=False)[:5]
            item.update({
                "dashboard_url": request.build_absolute_uri(reverse("dashboard-ai-agents")) + f"?agent={agent.id}",
                "test_url": request.build_absolute_uri(reverse("api-ai-agent-test", kwargs={"agent_id": agent.id})),
                "analytics_url": request.build_absolute_uri(reverse("api-ai-agent-analytics", kwargs={"agent_id": agent.id})),
                "knowledge_url": request.build_absolute_uri(reverse("api-ai-agent-knowledge", kwargs={"agent_id": agent.id})),
                "faqs_url": request.build_absolute_uri(reverse("api-ai-agent-faqs", kwargs={"agent_id": agent.id})),
                "leads_url": request.build_absolute_uri(reverse("api-ai-agent-leads", kwargs={"agent_id": agent.id})),
                "suggested_questions": public_agent_suggested_questions(agent),
                "knowledge_count": agent.knowledge_items.filter(is_active=True).count(),
                "faq_count": agent.faqs.filter(is_active=True).count(),
                "lead_count": agent.leads.count(),
                "conversation_count": agent.conversations.count(),
                "open_suggestions": [
                    {
                        "id": suggestion.id,
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "priority": suggestion.priority,
                        "action_label": suggestion.action_label,
                        "action_url": suggestion.action_url,
                    }
                    for suggestion in open_suggestions
                ],
                "analytics": {
                    "conversations": analytics.get("conversations", 0),
                    "leads": analytics.get("leads", 0),
                    "questions": analytics.get("questions", 0),
                    "unanswered": analytics.get("unanswered", 0),
                    "conversion_rate": analytics.get("conversion_rate", 0),
                },
            })
            enriched_agents.append(item)
        data = {
            "agents": enriched_agents,
            "dashboard_url": request.build_absolute_uri(reverse("dashboard-ai-agents")),
            "api_url": request.build_absolute_uri(reverse("api-ai-agent-list")),
        }
        return success_response("Mobile AI agents retrieved successfully.", data)


class MobileActionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {
            "native_actions": {
                "phone": "tel:{value}",
                "email": "mailto:{value}",
                "website": "{value}",
                "whatsapp": "https://wa.me/{value}",
                "maps": "https://www.google.com/maps/search/?api=1&query={value}",
                "share": "system_share",
                "download_contact": "vcf",
                "download_qr": "image_svg",
            },
            "share_templates": {
                "digital_card": "Conecta conmigo en Cardbook: {public_url}",
                "business_card": "Te comparto mi tarjeta de presentacion: {public_url}",
                "white_card_job": "Mira mi White Card Job en Cardbook: {public_url}",
                "company": "Conoce esta empresa en Cardbook: {public_url}",
            },
        }
        return success_response("Mobile actions retrieved successfully.", data)
