from dataclasses import dataclass
from datetime import timedelta
from collections import Counter

from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from alliances.models import CompanyAlliance
from business_feed.models import BusinessPost
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from websitebuilder.models import Website

from .models import AIAgent, AIAgentConversation, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead, AIAgentMessage, AIAgentSuggestion


@dataclass(frozen=True)
class AgentRecommendation:
    key: str
    title: str
    description: str
    priority: str = AIAgentSuggestion.PRIORITY_MEDIUM
    action_label: str = ""
    action_url: str = ""


def get_user_companies(user):
    if user.is_superuser:
        return Company.objects.filter(is_active=True)
    return (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
    ).distinct()


def get_or_create_company_agent(company, user=None, agent_type=AIAgent.TYPE_BUSINESS_ASSISTANT):
    defaults = {
        "created_by": user if user and user.is_authenticated else None,
        "name": f"Asistente de {company.name}",
        "mode": AIAgent.MODE_RULE_BASED,
        "status": AIAgent.STATUS_ACTIVE,
        "welcome_message": f"Hola, soy el asistente de {company.name}. Puedo ayudarte a completar tu presencia digital.",
    }
    agent, _ = AIAgent.objects.get_or_create(company=company, agent_type=agent_type, defaults=defaults)
    return agent


def sync_agents_for_user(user):
    agents = []
    for company in get_user_companies(user):
        agents.append(get_or_create_company_agent(company, user=user))
        agents.append(get_or_create_company_agent(company, user=user, agent_type=AIAgent.TYPE_WEBSITE_ASSISTANT))
    return agents


def company_completion_score(company):
    checks = [
        bool(company.logo),
        bool(company.description),
        bool(company.phone_number),
        bool(company.email),
        bool(company.website),
        bool(company.category),
        bool(company.services),
        DigitalCard.objects.filter(company=company, is_active=True).exists(),
        BusinessCard.objects.filter(profile__company=company, is_active=True).exists(),
        Website.objects.filter(company=company, is_active=True, is_published=True).exists(),
    ]
    completed = sum(1 for item in checks if item)
    return int((completed / len(checks)) * 100)


def analyze_company(company):
    recommendations = []

    if not company.logo:
        recommendations.append(AgentRecommendation(
            key="logo",
            title="Agrega un logo profesional",
            description="El logo hace que tus tarjetas, website y marketplace se vean mas confiables.",
            priority=AIAgentSuggestion.PRIORITY_HIGH,
            action_label="Editar empresa",
            action_url=reverse("dashboard-company-update", args=[company.id]),
        ))
    if not company.description:
        recommendations.append(AgentRecommendation(
            key="description",
            title="Completa la descripcion de la empresa",
            description="Una descripcion clara ayuda al visitante a entender que haces y por que contactarte.",
            priority=AIAgentSuggestion.PRIORITY_HIGH,
            action_label="Editar empresa",
            action_url=reverse("dashboard-company-update", args=[company.id]),
        ))
    if not company.services:
        recommendations.append(AgentRecommendation(
            key="services",
            title="Define tus servicios principales",
            description="El agente publico y el marketplace usan tus servicios para responder mejor y recomendarte.",
            priority=AIAgentSuggestion.PRIORITY_MEDIUM,
            action_label="Editar servicios",
            action_url=reverse("dashboard-company-update", args=[company.id]),
        ))
    if not company.phone_number and not company.email:
        recommendations.append(AgentRecommendation(
            key="contact",
            title="Agrega informacion de contacto",
            description="Sin telefono o email, el agente no podra convertir visitantes en clientes.",
            priority=AIAgentSuggestion.PRIORITY_HIGH,
            action_label="Completar contacto",
            action_url=reverse("dashboard-company-update", args=[company.id]),
        ))
    if not DigitalCard.objects.filter(company=company, is_active=True).exists():
        recommendations.append(AgentRecommendation(
            key="profile",
            title="Crea el perfil del negocio",
            description="El perfil digital es la pieza base para compartir tu empresa con QR y enlaces.",
            priority=AIAgentSuggestion.PRIORITY_MEDIUM,
            action_label="Crear perfil",
            action_url=reverse("dashboard-card-create"),
        ))
    if not BusinessCard.objects.filter(profile__company=company, is_active=True).exists():
        recommendations.append(AgentRecommendation(
            key="business_card",
            title="Crea tarjetas de presentacion",
            description="Las tarjetas de empleados ayudan a compartir contactos de forma elegante y profesional.",
            priority=AIAgentSuggestion.PRIORITY_MEDIUM,
            action_label="Crear presentacion",
            action_url=reverse("dashboard-business-card-create"),
        ))
    if not Website.objects.filter(company=company, is_active=True, is_published=True).exists():
        recommendations.append(AgentRecommendation(
            key="website",
            title="Publica tu website empresarial",
            description="El website activa una presencia publica mas completa para tus visitantes.",
            priority=AIAgentSuggestion.PRIORITY_MEDIUM,
            action_label="Abrir Website Builder",
            action_url=reverse("dashboard-company-website", args=[company.id]),
        ))
    if not BusinessPost.objects.filter(company=company, is_active=True).exists():
        recommendations.append(AgentRecommendation(
            key="first_post",
            title="Publica una novedad empresarial",
            description="Una primera publicacion hace que tu empresa se vea activa y ayuda a generar confianza.",
            priority=AIAgentSuggestion.PRIORITY_LOW,
            action_label="Crear publicacion",
            action_url=f"{reverse('dashboard-companies')}?company={company.id}#publicaciones",
        ))
    has_alliance = CompanyAlliance.objects.filter(requester=company, status=CompanyAlliance.STATUS_ACCEPTED).exists() or CompanyAlliance.objects.filter(
        receiver=company,
        status=CompanyAlliance.STATUS_ACCEPTED,
    ).exists()
    if not has_alliance:
        recommendations.append(AgentRecommendation(
            key="alliances",
            title="Busca una alianza estrategica",
            description="Las alianzas conectan tu empresa con negocios afines y fortalecen tu visibilidad en Cardbook.",
            priority=AIAgentSuggestion.PRIORITY_LOW,
            action_label="Ver sugeridas",
            action_url=f"{reverse('dashboard-companies')}?company={company.id}#sugeridas",
        ))

    return recommendations


def refresh_suggestions(agent):
    if not agent.company_id:
        return []
    company = agent.company
    recommendations = analyze_company(company)
    for recommendation in recommendations:
        AIAgentSuggestion.objects.update_or_create(
            agent=agent,
            company=company,
            title=recommendation.title,
            defaults={
                "description": recommendation.description,
                "priority": recommendation.priority,
                "action_label": recommendation.action_label,
                "action_url": recommendation.action_url,
                "is_resolved": False,
            },
        )
    agent.suggestions.exclude(title__in=[item.title for item in recommendations]).update(is_resolved=True)
    return [item.key for item in recommendations]


def _upsert_knowledge(agent, *, source, category, title, content):
    content = (content or "").strip()
    if not content:
        return None
    item, _ = AIAgentKnowledgeBase.objects.update_or_create(
        agent=agent,
        title=title,
        defaults={
            "category": category,
            "content": content,
            "is_public": True,
            "is_active": True,
        },
    )
    return item


def sync_agent_knowledge(agent):
    if not agent.company_id:
        return []

    company = agent.company
    created_or_updated = []
    created_or_updated.append(_upsert_knowledge(
        agent,
        source="company_profile",
        category=AIAgentKnowledgeBase.CATEGORY_GENERAL,
        title="Perfil de la empresa",
        content="\n".join(filter(None, [company.name, company.description, company.category])),
    ))
    created_or_updated.append(_upsert_knowledge(
        agent,
        source="company_services",
        category=AIAgentKnowledgeBase.CATEGORY_SERVICES,
        title="Servicios principales",
        content=company.services,
    ))
    created_or_updated.append(_upsert_knowledge(
        agent,
        source="company_contact",
        category=AIAgentKnowledgeBase.CATEGORY_GENERAL,
        title="Contacto de la empresa",
        content="\n".join(filter(None, [
            f"Telefono: {company.phone_number}" if company.phone_number else "",
            f"Email: {company.email}" if company.email else "",
            f"Website: {company.website}" if company.website else "",
            f"Ubicacion: {company.city}" if company.city else "",
        ])),
    ))

    website = Website.objects.filter(company=company, is_active=True).prefetch_related("pages__layout__sections").first()
    if website:
        agent.website = website
        agent.save(update_fields=["website", "updated_at"])
        created_or_updated.append(_upsert_knowledge(
            agent,
            source="website_meta",
            category=AIAgentKnowledgeBase.CATEGORY_GENERAL,
            title="Website publico",
            content="\n".join(filter(None, [website.title, website.meta_description, website.domain or website.subdomain])),
        ))
        for page in website.pages.filter(is_active=True, is_published=True):
            if not hasattr(page, "layout"):
                continue
            for section in page.layout.sections.filter(is_active=True).order_by("order", "id")[:8]:
                created_or_updated.append(_upsert_knowledge(
                    agent,
                    source=f"website_section:{section.id}",
                    category=AIAgentKnowledgeBase.CATEGORY_GENERAL,
                    title=f"Website - {page.title} - {section.name}",
                    content="\n".join(filter(None, [section.title, section.subtitle])),
                ))

    return [item for item in created_or_updated if item]


def answer_from_knowledge(agent, question):
    query = (question or "").strip().lower()
    if not query:
        return agent.fallback_message

    faqs = AIAgentFAQ.objects.filter(agent=agent, is_active=True, is_public=True)
    for faq in faqs:
        searchable = " ".join([faq.question, faq.keywords, faq.answer]).lower()
        if query in searchable or any(word and word in searchable for word in query.split()):
            return faq.answer

    items = AIAgentKnowledgeBase.objects.filter(agent=agent, is_active=True, is_public=True)
    for item in items:
        searchable = " ".join([item.title, item.content]).lower()
        if query in searchable or any(word and word in searchable for word in query.split()):
            return item.content
    return agent.fallback_message


def public_agent_suggested_questions(agent, limit=4):
    if not agent:
        return []
    questions = []
    if agent.company and agent.company.services:
        questions.append("Que servicios ofrecen?")
    if agent.knowledge_items.filter(category=AIAgentKnowledgeBase.CATEGORY_PRICING, is_active=True, is_public=True).exists():
        questions.append("Cuales son sus precios?")
    if agent.knowledge_items.filter(category=AIAgentKnowledgeBase.CATEGORY_HOURS, is_active=True, is_public=True).exists():
        questions.append("Cual es su horario?")
    if agent.company and (agent.company.phone_number or agent.company.email or agent.company.website):
        questions.append("Como puedo contactarlos?")
    for faq in agent.faqs.filter(is_active=True, is_public=True).order_by("question")[:limit]:
        if faq.question not in questions:
            questions.append(faq.question)
    fallback_questions = [
        "Que hace esta empresa?",
        "Como puedo solicitar informacion?",
        "Tienen servicios para mi negocio?",
        "Puedo hablar con alguien?",
    ]
    for question in fallback_questions:
        if len(questions) >= limit:
            break
        if question not in questions:
            questions.append(question)
    return questions[:limit]


def agent_analytics(agent, days=14):
    if not agent:
        return {
            "days": days,
            "conversations": 0,
            "leads": 0,
            "converted_leads": 0,
            "conversion_rate": 0,
            "questions": 0,
            "unanswered": 0,
            "timeline": [],
            "lead_statuses": [],
            "top_questions": [],
        }

    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)
    conversations = agent.conversations.filter(created_at__date__gte=start_date)
    leads = agent.leads.filter(created_at__date__gte=start_date)
    messages = AIAgentMessage.objects.filter(conversation__agent=agent, created_at__date__gte=start_date)

    conversation_rows = {
        item["created_at__date"]: item["total"]
        for item in conversations.values("created_at__date").annotate(total=Count("id"))
    }
    lead_rows = {
        item["created_at__date"]: item["total"]
        for item in leads.values("created_at__date").annotate(total=Count("id"))
    }
    timeline = []
    for index in range(days):
        day = start_date + timedelta(days=index)
        timeline.append({
            "date": day,
            "label": day.strftime("%d/%m"),
            "conversations": conversation_rows.get(day, 0),
            "leads": lead_rows.get(day, 0),
        })

    status_counts = {
        item["status"]: item["total"]
        for item in leads.values("status").annotate(total=Count("id"))
    }
    lead_statuses = [
        {"value": value, "label": label, "total": status_counts.get(value, 0)}
        for value, label in AIAgentLead.STATUS_CHOICES
    ]

    question_counter = Counter()
    question_labels = {}
    for content in messages.filter(role=AIAgentMessage.ROLE_USER).values_list("content", flat=True):
        label = (content or "").strip()
        if not label:
            continue
        key = " ".join(label.lower().split())
        question_counter[key] += 1
        question_labels.setdefault(key, label[:90])

    top_questions = [
        {"question": question_labels[key], "total": total}
        for key, total in question_counter.most_common(5)
    ]

    total_conversations = conversations.count()
    total_leads = leads.count()
    converted_leads = leads.filter(status=AIAgentLead.STATUS_CONVERTED).count()
    conversion_rate = round((converted_leads / total_leads) * 100) if total_leads else 0
    unanswered = messages.filter(role=AIAgentMessage.ROLE_AGENT, content=agent.fallback_message).count()

    return {
        "days": days,
        "conversations": total_conversations,
        "leads": total_leads,
        "converted_leads": converted_leads,
        "conversion_rate": conversion_rate,
        "questions": messages.filter(role=AIAgentMessage.ROLE_USER).count(),
        "unanswered": unanswered,
        "timeline": timeline,
        "lead_statuses": lead_statuses,
        "top_questions": top_questions,
    }


def agent_unanswered_questions(agent, limit=6):
    if not agent:
        return []

    known_questions = {
        " ".join(question.lower().split())
        for question in agent.faqs.filter(is_active=True).values_list("question", flat=True)
    }
    counter = Counter()
    labels = {}
    latest_seen = {}
    conversations = (
        agent.conversations
        .filter(messages__role=AIAgentMessage.ROLE_AGENT, messages__content=agent.fallback_message)
        .prefetch_related("messages")
        .distinct()[:60]
    )

    for conversation in conversations:
        previous_user_message = ""
        previous_created_at = None
        for message in conversation.messages.all():
            if message.role == AIAgentMessage.ROLE_USER:
                previous_user_message = (message.content or "").strip()
                previous_created_at = message.created_at
                continue
            if (
                message.role == AIAgentMessage.ROLE_AGENT
                and message.content == agent.fallback_message
                and previous_user_message
            ):
                key = " ".join(previous_user_message.lower().split())
                if key in known_questions:
                    continue
                counter[key] += 1
                labels.setdefault(key, previous_user_message)
                latest_seen[key] = max(latest_seen.get(key, previous_created_at), previous_created_at)

    items = []
    for key, total in counter.most_common(limit):
        items.append({
            "question": labels.get(key, key)[:140],
            "label": labels.get(key, key)[:90],
            "total": total,
            "latest": latest_seen.get(key),
        })
    return items


def dashboard_agent_summary(user):
    agents = sync_agents_for_user(user)
    company_ids = [agent.company_id for agent in agents if agent.company_id]
    stats = {
        "agents": len(agents),
        "active": sum(1 for agent in agents if agent.status == AIAgent.STATUS_ACTIVE and agent.is_active),
        "companies": len(set(company_ids)),
        "leads": 0,
        "conversations": 0,
        "suggestions": 0,
    }
    if agents:
        queryset = AIAgent.objects.filter(pk__in=[agent.pk for agent in agents]).annotate(
            lead_total=Count("leads", distinct=True),
            conversation_total=Count("conversations", distinct=True),
            suggestion_total=Count("suggestions", distinct=True),
        )
        stats["leads"] = sum(agent.lead_total for agent in queryset)
        stats["conversations"] = sum(agent.conversation_total for agent in queryset)
        stats["suggestions"] = sum(agent.suggestion_total for agent in queryset)
    return stats


def business_assistant_context(user, company=None, limit=4):
    companies = get_user_companies(user)
    active_company = company or companies.first()
    if not active_company:
        return {
            "available": False,
            "company": None,
            "agent": None,
            "score": 0,
            "status_label": "Sin empresa",
            "status_detail": "Crea una empresa para activar tu asistente de negocio.",
            "suggestions": [],
            "top_suggestion": None,
        }

    agent = get_or_create_company_agent(active_company, user=user, agent_type=AIAgent.TYPE_BUSINESS_ASSISTANT)
    refresh_suggestions(agent)
    score = company_completion_score(active_company)
    suggestions = list(agent.suggestions.filter(is_resolved=False)[:limit])

    if score >= 85:
        status_label = "Presencia solida"
        status_detail = "Tu empresa ya tiene una base fuerte. El siguiente paso es publicar y medir resultados."
    elif score >= 55:
        status_label = "Buen avance"
        status_detail = "Ya tienes una base funcional. Completa los puntos pendientes para verte mas profesional."
    else:
        status_label = "Necesita impulso"
        status_detail = "El asistente detecto piezas importantes pendientes para activar mejor tu presencia digital."

    return {
        "available": True,
        "company": active_company,
        "agent": agent,
        "score": score,
        "status_label": status_label,
        "status_detail": status_detail,
        "suggestions": suggestions,
        "top_suggestion": suggestions[0] if suggestions else None,
    }
