from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from rest_framework.test import APIClient

from companies.models import Company
from referrals.models import ReferralNotification
from websitebuilder.models import Page
from websitebuilder.services import create_starter_website

from .guides import get_dashboard_guide_payload
from .models import AIAgent, AIAgentConversation, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead, AIAgentMessage
from .security import ASK_LIMIT
from .services import (
    agent_analytics,
    agent_unanswered_questions,
    answer_from_knowledge,
    business_assistant_context,
    company_completion_score,
    sync_agent_knowledge,
    public_agent_suggested_questions,
    sync_agents_for_user,
)


class AIAgentDashboardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="agent-owner",
            email="agent-owner@example.com",
            password="pass12345",
        )
        self.company = Company.objects.create(
            owner=self.user,
            name="Agent Demo LLC",
            description="Empresa demo para agentes.",
            email="hello@example.com",
            phone_number="555-0101",
            category="Tecnologia",
            services="Websites, tarjetas digitales",
        )

    def test_sync_agents_for_user_creates_business_and_website_agents(self):
        agents = sync_agents_for_user(self.user)

        self.assertEqual(len(agents), 2)
        self.assertTrue(
            AIAgent.objects.filter(company=self.company, agent_type=AIAgent.TYPE_BUSINESS_ASSISTANT).exists()
        )
        self.assertTrue(
            AIAgent.objects.filter(company=self.company, agent_type=AIAgent.TYPE_WEBSITE_ASSISTANT).exists()
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard-ai-agents"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_dashboard_renders_for_company_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard-ai-agents"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agentes IA")
        self.assertContains(response, "Agent Demo LLC")

    def test_completion_score_returns_percentage(self):
        score = company_completion_score(self.company)

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_business_assistant_context_returns_actionable_suggestion(self):
        context = business_assistant_context(self.user, self.company)

        self.assertTrue(context["available"])
        self.assertEqual(context["company"], self.company)
        self.assertIsNotNone(context["agent"])
        self.assertGreater(len(context["suggestions"]), 0)
        self.assertIsNotNone(context["top_suggestion"])

    def test_dashboard_home_renders_business_assistant_card(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asistente de negocio")
        self.assertContains(response, "Agent Demo LLC")

    def test_dashboard_guide_payload_is_contextual(self):
        request = self.factory.get(reverse("dashboard-home"))
        request.user = self.user
        request.resolver_match = resolve(reverse("dashboard-home"))

        payload = get_dashboard_guide_payload(request)

        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["route"], "dashboard-home")
        self.assertGreater(payload["total"], 0)

    def test_dashboard_home_renders_guide_widget(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ai-guide-data")
        self.assertContains(response, "data-ai-guide")

    def test_sync_agent_knowledge_creates_company_items(self):
        agent = sync_agents_for_user(self.user)[0]

        items = sync_agent_knowledge(agent)

        self.assertGreaterEqual(len(items), 2)
        self.assertTrue(AIAgentKnowledgeBase.objects.filter(agent=agent, title="Perfil de la empresa").exists())
        self.assertTrue(AIAgentKnowledgeBase.objects.filter(agent=agent, title="Servicios principales").exists())

    def test_answer_from_knowledge_uses_faq_first(self):
        agent = sync_agents_for_user(self.user)[0]
        AIAgentFAQ.objects.create(
            agent=agent,
            question="Cuanto cuesta una tarjeta?",
            answer="Tenemos planes flexibles para tarjetas digitales.",
            keywords="precio, costo, tarjeta",
        )

        answer = answer_from_knowledge(agent, "precio")

        self.assertEqual(answer, "Tenemos planes flexibles para tarjetas digitales.")

    def test_dashboard_can_create_knowledge_item(self):
        agent = sync_agents_for_user(self.user)[0]
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard-ai-agents"), {
            "action": "create_knowledge",
            "agent": agent.id,
            "category": AIAgentKnowledgeBase.CATEGORY_POLICY,
            "title": "Politica de garantia",
            "content": "La garantia depende del servicio contratado.",
            "is_public": "on",
            "is_active": "on",
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(AIAgentKnowledgeBase.objects.filter(agent=agent, title="Politica de garantia").exists())

    def test_public_agent_endpoint_answers_and_stores_conversation(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.agent_type = AIAgent.TYPE_WEBSITE_ASSISTANT
        agent.show_on_website = True
        agent.save(update_fields=["agent_type", "show_on_website", "updated_at"])
        AIAgentFAQ.objects.create(
            agent=agent,
            question="Que servicios ofrecen?",
            answer="Ofrecemos websites, tarjetas digitales y perfiles profesionales.",
            keywords="servicios, websites, tarjetas",
        )

        response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "message": "servicios",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("websites", response.json()["answer"])
        self.assertEqual(AIAgentConversation.objects.filter(agent=agent).count(), 1)
        self.assertEqual(AIAgentMessage.objects.filter(conversation__agent=agent).count(), 2)

    def test_public_agent_endpoint_captures_lead(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.show_on_website = True
        agent.can_capture_leads = True
        agent.save(update_fields=["show_on_website", "can_capture_leads", "updated_at"])

        response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "name": "Maria Cliente",
            "email": "maria@example.com",
            "phone": "555-9090",
            "service_interest": "Website empresarial",
            "message": "Necesito una cotizacion.",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        lead = AIAgentLead.objects.get(agent=agent)
        self.assertEqual(lead.name, "Maria Cliente")
        self.assertEqual(lead.service_interest, "Website empresarial")
        self.assertEqual(lead.conversation.status, AIAgentConversation.STATUS_LEAD)
        self.assertTrue(
            ReferralNotification.objects.filter(
                recipient=self.user,
                event_type=ReferralNotification.TYPE_AI_LEAD,
                data__lead_id=lead.id,
                read_at__isnull=True,
            ).exists()
        )

    def test_notification_inbox_links_to_ai_lead_detail(self):
        agent = sync_agents_for_user(self.user)[1]
        lead = AIAgentLead.objects.create(
            agent=agent,
            company=self.company,
            name="Lead Notificado",
            email="notificado@example.com",
            service_interest="Website",
        )
        ReferralNotification.objects.create(
            recipient=self.user,
            event_type=ReferralNotification.TYPE_AI_LEAD,
            title="Nuevo lead del agente IA",
            message="Lead Notificado dejo sus datos.",
            data={
                "lead_id": lead.id,
                "agent_id": agent.id,
                "company_id": self.company.id,
                "action_url": f"{reverse('dashboard-ai-agents')}?agent={agent.id}#leads",
            },
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard-notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo lead del agente IA")
        self.assertContains(response, "Ver detalle")

    def test_public_agent_rejects_lead_without_contact_method(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.show_on_website = True
        agent.can_capture_leads = True
        agent.save(update_fields=["show_on_website", "can_capture_leads", "updated_at"])

        response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "name": "Sin Contacto",
            "message": "Quiero informacion.",
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(AIAgentLead.objects.filter(agent=agent).exists())

    def test_public_agent_rejects_lead_honeypot(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.show_on_website = True
        agent.can_capture_leads = True
        agent.save(update_fields=["show_on_website", "can_capture_leads", "updated_at"])

        response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "name": "Bot",
            "email": "bot@example.com",
            "website_url": "https://spam.example.com",
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(AIAgentLead.objects.filter(agent=agent).exists())

    def test_public_agent_rejects_invalid_email_and_phone(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.show_on_website = True
        agent.can_capture_leads = True
        agent.save(update_fields=["show_on_website", "can_capture_leads", "updated_at"])

        email_response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "email": "correo-invalido",
        })
        phone_response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "intent": "lead",
            "phone": "12",
        })

        self.assertEqual(email_response.status_code, 400)
        self.assertEqual(phone_response.status_code, 400)
        self.assertFalse(AIAgentLead.objects.filter(agent=agent).exists())

    def test_public_agent_rate_limits_questions(self):
        agent = sync_agents_for_user(self.user)[1]
        agent.show_on_website = True
        agent.save(update_fields=["show_on_website", "updated_at"])

        for index in range(ASK_LIMIT):
            response = self.client.post(reverse("public-ai-agent-ask"), {
                "agent": agent.id,
                "message": f"Pregunta {index}",
            })
            self.assertEqual(response.status_code, 200)

        limited_response = self.client.post(reverse("public-ai-agent-ask"), {
            "agent": agent.id,
            "message": "Una pregunta mas",
        })

        self.assertEqual(limited_response.status_code, 429)

    def test_ai_agent_security_settings_are_configured(self):
        values = [
            settings.AI_AGENT_PUBLIC_ASK_LIMIT,
            settings.AI_AGENT_PUBLIC_ASK_WINDOW_SECONDS,
            settings.AI_AGENT_PUBLIC_LEAD_LIMIT,
            settings.AI_AGENT_PUBLIC_LEAD_WINDOW_SECONDS,
            settings.AI_AGENT_MAX_QUESTION_LENGTH,
            settings.AI_AGENT_MAX_LEAD_FIELD_LENGTH,
            settings.AI_AGENT_MAX_LEAD_MESSAGE_LENGTH,
        ]
        self.assertTrue(all(isinstance(value, int) and value > 0 for value in values))

    def test_dashboard_can_update_lead_status(self):
        agent = sync_agents_for_user(self.user)[1]
        conversation = AIAgentConversation.objects.create(
            agent=agent,
            company=self.company,
            channel=AIAgentConversation.CHANNEL_WEBSITE,
            status=AIAgentConversation.STATUS_LEAD,
        )
        lead = AIAgentLead.objects.create(
            agent=agent,
            company=self.company,
            conversation=conversation,
            name="Lead Demo",
            email="lead@example.com",
            service_interest="Tarjeta digital",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard-ai-agents"), {
            "action": "update_lead_status",
            "agent": agent.id,
            "lead": lead.id,
            "status": AIAgentLead.STATUS_CONVERTED,
            "message": "Cliente convertido en prueba.",
        })

        self.assertEqual(response.status_code, 302)
        lead.refresh_from_db()
        conversation.refresh_from_db()
        self.assertEqual(lead.status, AIAgentLead.STATUS_CONVERTED)
        self.assertEqual(conversation.status, AIAgentConversation.STATUS_CLOSED)
        self.assertTrue(AIAgentMessage.objects.filter(conversation=conversation, intent="lead_status").exists())

    def test_dashboard_renders_lead_management_filters(self):
        agent = sync_agents_for_user(self.user)[1]
        AIAgentLead.objects.create(
            agent=agent,
            company=self.company,
            name="Filtro Lead",
            email="filtro@example.com",
            service_interest="Website",
            status=AIAgentLead.STATUS_CONTACTED,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard-ai-agents"), {
            "agent": agent.id,
            "lead_status": AIAgentLead.STATUS_CONTACTED,
            "lead_q": "Filtro",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion de leads")
        self.assertContains(response, "Analytics del agente")
        self.assertContains(response, "Filtro Lead")
        self.assertContains(response, "Contactado")

    def test_dashboard_agent_test_simulator_answers_from_faq(self):
        agent = sync_agents_for_user(self.user)[1]
        AIAgentFAQ.objects.create(
            agent=agent,
            question="Tienen planes para emprendedores?",
            answer="Si, tenemos planes para emprendedores y pequenas empresas.",
            keywords="planes, emprendedores",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard-ai-agents"), {
            "action": "test_agent_question",
            "agent": agent.id,
            "test_question": "planes emprendedores",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Probar agente")
        self.assertContains(response, "Respuesta encontrada")
        self.assertContains(response, "Si, tenemos planes para emprendedores")

    def test_agent_unanswered_questions_detects_fallback_gaps(self):
        agent = sync_agents_for_user(self.user)[1]
        conversation = AIAgentConversation.objects.create(
            agent=agent,
            company=self.company,
            channel=AIAgentConversation.CHANNEL_WEBSITE,
        )
        AIAgentMessage.objects.create(
            conversation=conversation,
            role=AIAgentMessage.ROLE_USER,
            content="Atienden emergencias los domingos?",
        )
        AIAgentMessage.objects.create(
            conversation=conversation,
            role=AIAgentMessage.ROLE_AGENT,
            content=agent.fallback_message,
        )

        gaps = agent_unanswered_questions(agent)

        self.assertEqual(gaps[0]["question"], "Atienden emergencias los domingos?")
        self.assertEqual(gaps[0]["total"], 1)

    def test_dashboard_can_train_faq_from_unanswered_question(self):
        agent = sync_agents_for_user(self.user)[1]
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard-ai-agents"), {
            "action": "create_faq_from_gap",
            "agent": agent.id,
            "question": "Atienden emergencias los domingos?",
            "answer": "Si, atendemos emergencias coordinadas los domingos.",
            "keywords": "emergencias, domingos",
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(AIAgentFAQ.objects.filter(
            agent=agent,
            question="Atienden emergencias los domingos?",
            answer__icontains="emergencias coordinadas",
            is_public=True,
            is_active=True,
        ).exists())

    def test_agent_analytics_summarizes_conversations_leads_and_questions(self):
        agent = sync_agents_for_user(self.user)[1]
        conversation = AIAgentConversation.objects.create(
            agent=agent,
            company=self.company,
            channel=AIAgentConversation.CHANNEL_WEBSITE,
            status=AIAgentConversation.STATUS_LEAD,
        )
        AIAgentMessage.objects.create(
            conversation=conversation,
            role=AIAgentMessage.ROLE_USER,
            content="Cuales son sus precios?",
            intent="pricing",
        )
        AIAgentMessage.objects.create(
            conversation=conversation,
            role=AIAgentMessage.ROLE_AGENT,
            content=agent.fallback_message,
            intent="fallback",
        )
        AIAgentLead.objects.create(
            agent=agent,
            company=self.company,
            conversation=conversation,
            name="Lead Convertido",
            email="convertido@example.com",
            status=AIAgentLead.STATUS_CONVERTED,
        )

        analytics = agent_analytics(agent)

        self.assertEqual(analytics["conversations"], 1)
        self.assertEqual(analytics["questions"], 1)
        self.assertEqual(analytics["leads"], 1)
        self.assertEqual(analytics["converted_leads"], 1)
        self.assertEqual(analytics["conversion_rate"], 100)
        self.assertEqual(analytics["unanswered"], 1)
        self.assertEqual(analytics["top_questions"][0]["question"], "Cuales son sus precios?")

    def test_public_website_renders_ai_widget_when_agent_is_visible(self):
        website = create_starter_website(self.company, publish=True)
        Page.objects.filter(website=website).update(is_published=True)
        agent = sync_agents_for_user(self.user)[1]
        agent.website = website
        agent.show_on_website = True
        agent.status = AIAgent.STATUS_ACTIVE
        agent.save(update_fields=["website", "show_on_website", "status", "updated_at"])

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-public-ai-agent")
        self.assertContains(response, "Quiero que me contacten")
        self.assertContains(response, "Que servicios ofrecen?")
        self.assertContains(response, "public_ai_agent.css")
        self.assertContains(response, "public_ai_agent.js")

    def test_public_agent_suggested_questions_uses_faqs(self):
        agent = sync_agents_for_user(self.user)[1]
        AIAgentFAQ.objects.create(
            agent=agent,
            question="Trabajan con pequenas empresas?",
            answer="Si, trabajamos con pequenas empresas.",
            keywords="pequenas, empresas",
        )

        questions = public_agent_suggested_questions(agent)

        self.assertIn("Que servicios ofrecen?", questions)
        self.assertIn("Trabajan con pequenas empresas?", questions)

    def test_api_lists_user_agents(self):
        sync_agents_for_user(self.user)
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.get(reverse("api-ai-agent-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["count"], 2)
        self.assertEqual(response.data["data"]["results"][0]["company_name"], self.company.name)

    def test_api_tests_agent_question(self):
        agent = sync_agents_for_user(self.user)[1]
        AIAgentFAQ.objects.create(
            agent=agent,
            question="Tienen soporte?",
            answer="Si, tenemos soporte para clientes activos.",
            keywords="soporte",
        )
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.post(reverse("api-ai-agent-test", kwargs={"agent_id": agent.id}), {
            "question": "soporte",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["used_fallback"])
        self.assertIn("soporte para clientes", response.data["data"]["answer"])

    def test_api_returns_agent_analytics_and_training_gaps(self):
        agent = sync_agents_for_user(self.user)[1]
        conversation = AIAgentConversation.objects.create(
            agent=agent,
            company=self.company,
            channel=AIAgentConversation.CHANNEL_MOBILE,
        )
        AIAgentMessage.objects.create(conversation=conversation, role=AIAgentMessage.ROLE_USER, content="Trabajan de noche?")
        AIAgentMessage.objects.create(conversation=conversation, role=AIAgentMessage.ROLE_AGENT, content=agent.fallback_message)
        client = APIClient()
        client.force_authenticate(self.user)

        analytics_response = client.get(reverse("api-ai-agent-analytics", kwargs={"agent_id": agent.id}))
        gaps_response = client.get(reverse("api-ai-agent-training-gaps", kwargs={"agent_id": agent.id}))

        self.assertEqual(analytics_response.status_code, 200)
        self.assertEqual(analytics_response.data["data"]["unanswered"], 1)
        self.assertEqual(gaps_response.status_code, 200)
        self.assertEqual(gaps_response.data["data"][0]["question"], "Trabajan de noche?")

    def test_api_can_train_faq_from_gap(self):
        agent = sync_agents_for_user(self.user)[1]
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.post(reverse("api-ai-agent-training-gaps", kwargs={"agent_id": agent.id}), {
            "question": "Tienen garantia?",
            "answer": "Si, cada servicio indica su garantia antes de contratar.",
            "keywords": "garantia",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(AIAgentFAQ.objects.filter(agent=agent, question="Tienen garantia?").exists())

    def test_api_prevents_managing_agent_without_permission(self):
        user_model = get_user_model()
        outsider = user_model.objects.create_user(username="outsider", password="pass12345")
        agent = sync_agents_for_user(self.user)[1]
        client = APIClient()
        client.force_authenticate(outsider)

        response = client.patch(reverse("api-ai-agent-detail", kwargs={"agent_id": agent.id}), {
            "name": "No permitido",
        }, format="json")

        self.assertEqual(response.status_code, 403)
