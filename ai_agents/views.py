import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views import View

from accesscontrol.services import PERM_MANAGE_AI_AGENTS, user_has_access_permission
from companies.permissions import can_manage_company

from .forms import AIAgentFAQForm, AIAgentKnowledgeBaseForm, AIAgentLeadStatusForm, AIAgentSettingsForm
from .models import AIAgent, AIAgentConversation, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead, AIAgentMessage
from .notifications import notify_ai_lead_created
from .security import (
    ASK_LIMIT,
    ASK_WINDOW_SECONDS,
    LEAD_LIMIT,
    LEAD_WINDOW_SECONDS,
    MAX_QUESTION_LENGTH,
    clean_message,
    clean_text,
    is_rate_limited,
    is_spam_honeypot,
    valid_email_or_blank,
    valid_phone_or_blank,
)
from .services import (
    agent_analytics,
    answer_from_knowledge,
    company_completion_score,
    agent_unanswered_questions,
    dashboard_agent_summary,
    get_user_companies,
    public_agent_suggested_questions,
    refresh_suggestions,
    sync_agent_knowledge,
    sync_agents_for_user,
)


def can_manage_agent(user, agent):
    if not agent or not agent.company:
        return bool(user and user.is_authenticated and user.is_superuser)
    return can_manage_company(user, agent.company) or user_has_access_permission(user, PERM_MANAGE_AI_AGENTS, agent.company)


def filtered_agent_leads(agent, *, lead_status="", query=""):
    leads = agent.leads.select_related("conversation").prefetch_related("conversation__messages")
    if lead_status:
        leads = leads.filter(status=lead_status)
    if query:
        leads = leads.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(service_interest__icontains=query)
            | Q(message__icontains=query)
        )
    return leads


class DashboardAIAgentsView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "dashboard/ai_agents/index.html"

    def get_companies(self):
        return get_user_companies(self.request.user)

    def get_active_agent(self):
        agent_id = self.request.GET.get("agent") or self.request.POST.get("agent")
        queryset = AIAgent.objects.filter(company__in=self.get_companies()).select_related("company", "website")
        if agent_id:
            agent = queryset.filter(pk=agent_id).first()
            if agent:
                return agent
        return queryset.order_by("company__name", "agent_type").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sync_agents_for_user(self.request.user)
        agents = AIAgent.objects.filter(company__in=self.get_companies()).select_related("company", "website").prefetch_related(
            "suggestions",
            "knowledge_items",
            "faqs",
        )
        active_agent = kwargs.get("active_agent") or self.get_active_agent()
        if active_agent:
            refresh_suggestions(active_agent)
            active_agent.refresh_from_db()
        lead_status = self.request.GET.get("lead_status", "")
        lead_query = (self.request.GET.get("lead_q") or "").strip()
        leads = AIAgentLead.objects.none()
        lead_stats = {}
        if active_agent:
            leads = filtered_agent_leads(active_agent, lead_status=lead_status, query=lead_query)
            lead_counts = active_agent.leads.values("status").annotate(total=Count("id"))
            lead_stats = {item["status"]: item["total"] for item in lead_counts}
        lead_stats_list = [
            {"value": value, "label": label, "total": lead_stats.get(value, 0)}
            for value, label in AIAgentLead.STATUS_CHOICES
        ]
        context.update({
            "agents": agents,
            "active_agent": active_agent,
            "agent_form": kwargs.get("agent_form") or (AIAgentSettingsForm(instance=active_agent) if active_agent else None),
            "knowledge_form": kwargs.get("knowledge_form") or AIAgentKnowledgeBaseForm(),
            "faq_form": kwargs.get("faq_form") or AIAgentFAQForm(),
            "lead_status_form": AIAgentLeadStatusForm(),
            "summary": dashboard_agent_summary(self.request.user),
            "completion_score": company_completion_score(active_agent.company) if active_agent and active_agent.company else 0,
            "open_suggestions": active_agent.suggestions.filter(is_resolved=False) if active_agent else [],
            "knowledge_items": active_agent.knowledge_items.all()[:12] if active_agent else [],
            "faq_items": active_agent.faqs.all()[:12] if active_agent else [],
            "lead_items": leads[:20],
            "lead_export_url": f"{reverse('dashboard-ai-agent-leads-csv')}?agent={active_agent.id}&lead_status={lead_status}&lead_q={lead_query}" if active_agent else "",
            "lead_status": lead_status,
            "lead_query": lead_query,
            "lead_stats": lead_stats,
            "lead_stats_list": lead_stats_list,
            "lead_status_choices": AIAgentLead.STATUS_CHOICES,
            "recent_leads": active_agent.leads.all()[:5] if active_agent else [],
            "recent_conversations": active_agent.conversations.all()[:5] if active_agent else [],
            "agent_analytics": agent_analytics(active_agent) if active_agent else agent_analytics(None),
            "agent_test_result": kwargs.get("agent_test_result"),
            "agent_test_suggestions": public_agent_suggested_questions(active_agent) if active_agent else [],
            "unanswered_questions": agent_unanswered_questions(active_agent) if active_agent else [],
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "sync_agents":
            sync_agents_for_user(request.user)
            messages.success(request, "Agentes sincronizados con tus empresas.")
            return redirect("dashboard-ai-agents")

        active_agent = get_object_or_404(AIAgent, pk=request.POST.get("agent"), company__in=self.get_companies())
        if not can_manage_agent(request.user, active_agent):
            messages.error(request, "No tienes permiso para configurar este agente.")
            return redirect("dashboard-ai-agents")

        if action == "update_agent":
            form = AIAgentSettingsForm(request.POST, instance=active_agent)
            if form.is_valid():
                form.save()
                messages.success(request, "Configuracion del agente actualizada.")
                return redirect(f"{request.path}?agent={active_agent.id}")
            return self.render_to_response(self.get_context_data(agent_form=form, active_agent=active_agent))

        if action == "refresh_suggestions":
            refresh_suggestions(active_agent)
            messages.success(request, "Recomendaciones actualizadas.")
            return redirect(f"{request.path}?agent={active_agent.id}")

        if action == "test_agent_question":
            question = (request.POST.get("test_question") or "").strip()
            if not question:
                messages.error(request, "Escribe una pregunta para probar el agente.")
                return redirect(f"{request.path}?agent={active_agent.id}#agent-test")
            answer = answer_from_knowledge(active_agent, question)
            test_result = {
                "question": question,
                "answer": answer,
                "used_fallback": answer == active_agent.fallback_message,
            }
            return self.render_to_response(self.get_context_data(active_agent=active_agent, agent_test_result=test_result))

        if action == "sync_knowledge":
            count = len(sync_agent_knowledge(active_agent))
            messages.success(request, f"Base de conocimiento sincronizada: {count} elementos.")
            return redirect(f"{request.path}?agent={active_agent.id}#knowledge")

        if action == "create_knowledge":
            form = AIAgentKnowledgeBaseForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.agent = active_agent
                item.save()
                messages.success(request, "Dato agregado a la base de conocimiento.")
                return redirect(f"{request.path}?agent={active_agent.id}#knowledge")
            return self.render_to_response(self.get_context_data(knowledge_form=form, active_agent=active_agent))

        if action == "update_knowledge":
            item = get_object_or_404(AIAgentKnowledgeBase, pk=request.POST.get("item"), agent=active_agent)
            form = AIAgentKnowledgeBaseForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                messages.success(request, "Dato de conocimiento actualizado.")
                return redirect(f"{request.path}?agent={active_agent.id}#knowledge")
            return self.render_to_response(self.get_context_data(knowledge_form=form, active_agent=active_agent))

        if action == "delete_knowledge":
            item = get_object_or_404(AIAgentKnowledgeBase, pk=request.POST.get("item"), agent=active_agent)
            item.delete()
            messages.success(request, "Dato de conocimiento eliminado.")
            return redirect(f"{request.path}?agent={active_agent.id}#knowledge")

        if action == "create_faq":
            form = AIAgentFAQForm(request.POST)
            if form.is_valid():
                faq = form.save(commit=False)
                faq.agent = active_agent
                faq.save()
                messages.success(request, "Pregunta frecuente agregada.")
                return redirect(f"{request.path}?agent={active_agent.id}#knowledge")
            return self.render_to_response(self.get_context_data(faq_form=form, active_agent=active_agent))

        if action == "create_faq_from_gap":
            question = (request.POST.get("question") or "").strip()
            answer = (request.POST.get("answer") or "").strip()
            keywords = (request.POST.get("keywords") or "").strip()
            if not question or not answer:
                messages.error(request, "La pregunta y la respuesta son obligatorias para entrenar el agente.")
                return redirect(f"{request.path}?agent={active_agent.id}#knowledge")
            AIAgentFAQ.objects.create(
                agent=active_agent,
                question=question[:255],
                answer=answer,
                keywords=keywords,
                is_public=True,
                is_active=True,
            )
            messages.success(request, "Pregunta entrenada y agregada como FAQ publica.")
            return redirect(f"{request.path}?agent={active_agent.id}#knowledge")

        if action == "update_faq":
            faq = get_object_or_404(AIAgentFAQ, pk=request.POST.get("faq"), agent=active_agent)
            form = AIAgentFAQForm(request.POST, instance=faq)
            if form.is_valid():
                form.save()
                messages.success(request, "Pregunta frecuente actualizada.")
                return redirect(f"{request.path}?agent={active_agent.id}#knowledge")
            return self.render_to_response(self.get_context_data(faq_form=form, active_agent=active_agent))

        if action == "delete_faq":
            faq = get_object_or_404(AIAgentFAQ, pk=request.POST.get("faq"), agent=active_agent)
            faq.delete()
            messages.success(request, "Pregunta frecuente eliminada.")
            return redirect(f"{request.path}?agent={active_agent.id}#knowledge")

        if action == "update_lead_status":
            lead = get_object_or_404(AIAgentLead, pk=request.POST.get("lead"), agent=active_agent)
            form = AIAgentLeadStatusForm(request.POST, instance=lead)
            if form.is_valid():
                form.save()
                if lead.conversation_id:
                    lead.conversation.status = AIAgentConversation.STATUS_LEAD if lead.status in {AIAgentLead.STATUS_NEW, AIAgentLead.STATUS_CONTACTED} else AIAgentConversation.STATUS_CLOSED
                    lead.conversation.save(update_fields=["status", "updated_at"])
                    AIAgentMessage.objects.create(
                        conversation=lead.conversation,
                        role=AIAgentMessage.ROLE_SYSTEM,
                        content=f"Lead actualizado a {lead.get_status_display()}.",
                        intent="lead_status",
                        metadata={"lead_id": lead.id, "status": lead.status},
                    )
                messages.success(request, "Lead actualizado.")
                return redirect(f"{request.path}?agent={active_agent.id}#leads")
            messages.error(request, "No se pudo actualizar el lead.")
            return redirect(f"{request.path}?agent={active_agent.id}#leads")

        messages.error(request, "Accion no reconocida.")
        return redirect("dashboard-ai-agents")


class DashboardAIAgentLeadsCSVView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get_companies(self):
        return get_user_companies(self.request.user)

    def get(self, request, *args, **kwargs):
        agent = get_object_or_404(
            AIAgent.objects.filter(company__in=self.get_companies()).select_related("company"),
            pk=request.GET.get("agent"),
        )
        if not can_manage_agent(request.user, agent):
            messages.error(request, "No tienes permiso para exportar leads de este agente.")
            return redirect("dashboard-ai-agents")

        leads = filtered_agent_leads(
            agent,
            lead_status=request.GET.get("lead_status", ""),
            query=(request.GET.get("lead_q") or "").strip(),
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="cardbook-ai-leads-{agent.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Fecha", "Empresa", "Agente", "Nombre", "Email", "Telefono", "Interes", "Estado", "Mensaje"])
        for lead in leads:
            writer.writerow([
                lead.id,
                lead.created_at.isoformat(),
                agent.company.name if agent.company else "",
                agent.name,
                lead.name,
                lead.email,
                lead.phone,
                lead.service_interest,
                lead.get_status_display(),
                lead.message,
            ])
        return response


@method_decorator(csrf_exempt, name="dispatch")
class PublicAIAgentAskView(View):
    def post(self, request, *args, **kwargs):
        agent = get_object_or_404(
            AIAgent.objects.select_related("company", "website"),
            pk=request.POST.get("agent"),
            agent_type=AIAgent.TYPE_WEBSITE_ASSISTANT,
            status=AIAgent.STATUS_ACTIVE,
            show_on_website=True,
            is_active=True,
        )
        if not request.session.session_key:
            request.session.create()

        conversation, _ = AIAgentConversation.objects.get_or_create(
            agent=agent,
            company=agent.company,
            website=agent.website,
            session_key=request.session.session_key,
            channel=AIAgentConversation.CHANNEL_WEBSITE,
            status=AIAgentConversation.STATUS_OPEN,
        )

        intent = request.POST.get("intent") or "ask"
        if intent == "lead":
            if is_spam_honeypot(request):
                return JsonResponse({"success": False, "message": "No pudimos procesar esta solicitud."}, status=400)
            if is_rate_limited(request, agent.id, "lead", LEAD_LIMIT, LEAD_WINDOW_SECONDS):
                return JsonResponse({"success": False, "message": "Has enviado varias solicitudes. Intentalo mas tarde."}, status=429)
            if not agent.can_capture_leads:
                return JsonResponse({"success": False, "message": "La captura de contactos no esta activa para este agente."}, status=400)
            name = clean_text(request.POST.get("name"))
            email = clean_text(request.POST.get("email"))
            phone = clean_text(request.POST.get("phone"))
            service_interest = clean_text(request.POST.get("service_interest"))
            message = clean_message(request.POST.get("message"))
            if not email and not phone:
                return JsonResponse({"success": False, "message": "Comparte un email o telefono para que podamos contactarte."}, status=400)
            if not valid_email_or_blank(email):
                return JsonResponse({"success": False, "message": "Escribe un email valido."}, status=400)
            if not valid_phone_or_blank(phone):
                return JsonResponse({"success": False, "message": "Escribe un telefono valido."}, status=400)
            lead = AIAgentLead.objects.create(
                agent=agent,
                company=agent.company,
                conversation=conversation,
                name=name,
                email=email,
                phone=phone,
                service_interest=service_interest,
                message=message,
            )
            conversation.visitor_name = name
            conversation.visitor_email = email
            conversation.visitor_phone = phone
            conversation.status = AIAgentConversation.STATUS_LEAD
            conversation.save(update_fields=["visitor_name", "visitor_email", "visitor_phone", "status", "updated_at"])
            AIAgentMessage.objects.create(
                conversation=conversation,
                role=AIAgentMessage.ROLE_SYSTEM,
                content=f"Lead capturado: {lead}",
                intent="lead_capture",
                metadata={"lead_id": lead.id, "service_interest": service_interest},
            )
            notify_ai_lead_created(lead)
            return JsonResponse({
                "success": True,
                "lead_id": lead.id,
                "answer": "Gracias. La empresa recibio tus datos y podra contactarte pronto.",
            })

        if is_rate_limited(request, agent.id, "ask", ASK_LIMIT, ASK_WINDOW_SECONDS):
            return JsonResponse({"success": False, "message": "El asistente recibio demasiados mensajes. Intentalo en un minuto."}, status=429)

        question = clean_text(request.POST.get("message"), max_length=MAX_QUESTION_LENGTH)
        if not question:
            return JsonResponse({"success": False, "message": "Escribe una pregunta para el agente."}, status=400)

        AIAgentMessage.objects.create(conversation=conversation, role=AIAgentMessage.ROLE_USER, content=question)
        answer = answer_from_knowledge(agent, question)
        AIAgentMessage.objects.create(
            conversation=conversation,
            role=AIAgentMessage.ROLE_AGENT,
            content=answer,
            metadata={"mode": agent.mode, "source": "knowledge_base"},
        )
        return JsonResponse({
            "success": True,
            "answer": answer,
            "can_capture_leads": agent.can_capture_leads,
            "lead_prompt": answer == agent.fallback_message and agent.can_capture_leads,
            "agent": agent.name,
            "company": agent.company.name if agent.company else "",
        })
