from rest_framework import permissions, status
from rest_framework.views import APIView

from accesscontrol.services import PERM_MANAGE_AI_AGENTS, user_has_access_permission
from cardbookweb.responses import StandardPagination, error_response, success_response
from companies.permissions import can_access_company, can_manage_company

from .api_serializers import (
    AIAgentFAQSerializer,
    AIAgentKnowledgeSerializer,
    AIAgentLeadSerializer,
    AIAgentSerializer,
    AIAgentTestQuestionSerializer,
    AIAgentTrainFAQSerializer,
)
from .models import AIAgent, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead
from .services import (
    agent_analytics,
    agent_unanswered_questions,
    answer_from_knowledge,
    get_user_companies,
    public_agent_suggested_questions,
    sync_agent_knowledge,
    sync_agents_for_user,
)


def user_agent_queryset(user):
    return AIAgent.objects.filter(company__in=get_user_companies(user)).select_related("company", "website")


def get_user_agent(user, pk):
    try:
        return user_agent_queryset(user).get(pk=pk)
    except AIAgent.DoesNotExist:
        return None


def can_manage_agent(user, agent):
    return bool(
        agent
        and agent.company
        and (can_manage_company(user, agent.company) or user_has_access_permission(user, PERM_MANAGE_AI_AGENTS, agent.company))
    )


class AIAgentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sync_agents_for_user(request.user)
        queryset = user_agent_queryset(request.user)
        company_id = request.query_params.get("company")
        agent_type = request.query_params.get("agent_type")
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if agent_type:
            queryset = queryset.filter(agent_type=agent_type)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AIAgentSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class AIAgentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent or not can_access_company(request.user, agent.company):
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        data = AIAgentSerializer(agent, context={"request": request}).data
        data["suggested_questions"] = public_agent_suggested_questions(agent)
        return success_response("Agent retrieved successfully.", data)

    def patch(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not can_manage_agent(request.user, agent):
            return error_response("You do not have permission to edit this agent.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = AIAgentSerializer(agent, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Agent update failed.", serializer.errors)
        serializer.save()
        return success_response("Agent updated successfully.", serializer.data)


class AIAgentAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        days = request.query_params.get("days", 14)
        try:
            days = max(1, min(int(days), 60))
        except (TypeError, ValueError):
            days = 14
        return success_response("Agent analytics retrieved successfully.", agent_analytics(agent, days=days))


class AIAgentTestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AIAgentTestQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Question is required.", serializer.errors)
        question = serializer.validated_data["question"]
        answer = answer_from_knowledge(agent, question)
        return success_response("Agent test completed successfully.", {
            "question": question,
            "answer": answer,
            "used_fallback": answer == agent.fallback_message,
            "can_capture_leads": agent.can_capture_leads,
        })


class AIAgentKnowledgeListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        queryset = agent.knowledge_items.all()
        serializer = AIAgentKnowledgeSerializer(queryset, many=True, context={"request": request})
        return success_response("Knowledge retrieved successfully.", serializer.data)

    def post(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not can_manage_agent(request.user, agent):
            return error_response("You do not have permission to manage this agent.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = AIAgentKnowledgeSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Knowledge creation failed.", serializer.errors)
        item = serializer.save(agent=agent)
        return success_response(
            "Knowledge created successfully.",
            AIAgentKnowledgeSerializer(item, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class AIAgentKnowledgeDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, agent_id, item_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return None
        return AIAgentKnowledgeBase.objects.filter(pk=item_id, agent=agent).first()

    def patch(self, request, agent_id, item_id):
        item = self.get_object(request, agent_id, item_id)
        if not item or not can_manage_agent(request.user, item.agent):
            return error_response("Knowledge item not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AIAgentKnowledgeSerializer(item, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Knowledge update failed.", serializer.errors)
        serializer.save()
        return success_response("Knowledge updated successfully.", serializer.data)

    def delete(self, request, agent_id, item_id):
        item = self.get_object(request, agent_id, item_id)
        if not item or not can_manage_agent(request.user, item.agent):
            return error_response("Knowledge item not found.", status_code=status.HTTP_404_NOT_FOUND)
        item.delete()
        return success_response("Knowledge deleted successfully.")


class AIAgentFAQListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AIAgentFAQSerializer(agent.faqs.all(), many=True, context={"request": request})
        return success_response("FAQ retrieved successfully.", serializer.data)

    def post(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not can_manage_agent(request.user, agent):
            return error_response("You do not have permission to manage this agent.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = AIAgentFAQSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("FAQ creation failed.", serializer.errors)
        faq = serializer.save(agent=agent)
        return success_response("FAQ created successfully.", AIAgentFAQSerializer(faq).data, status.HTTP_201_CREATED)


class AIAgentFAQDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, agent_id, faq_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return None
        return AIAgentFAQ.objects.filter(pk=faq_id, agent=agent).first()

    def patch(self, request, agent_id, faq_id):
        faq = self.get_object(request, agent_id, faq_id)
        if not faq or not can_manage_agent(request.user, faq.agent):
            return error_response("FAQ not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AIAgentFAQSerializer(faq, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("FAQ update failed.", serializer.errors)
        serializer.save()
        return success_response("FAQ updated successfully.", serializer.data)

    def delete(self, request, agent_id, faq_id):
        faq = self.get_object(request, agent_id, faq_id)
        if not faq or not can_manage_agent(request.user, faq.agent):
            return error_response("FAQ not found.", status_code=status.HTTP_404_NOT_FOUND)
        faq.delete()
        return success_response("FAQ deleted successfully.")


class AIAgentLeadsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        queryset = agent.leads.all()
        lead_status = request.query_params.get("status")
        if lead_status:
            queryset = queryset.filter(status=lead_status)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AIAgentLeadSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class AIAgentLeadDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, agent_id, lead_id):
        agent = get_user_agent(request.user, agent_id)
        lead = AIAgentLead.objects.filter(pk=lead_id, agent=agent).first() if agent else None
        if not lead or not can_manage_agent(request.user, agent):
            return error_response("Lead not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = AIAgentLeadSerializer(lead, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Lead update failed.", serializer.errors)
        serializer.save()
        return success_response("Lead updated successfully.", serializer.data)


class AIAgentTrainingGapsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not agent:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Training gaps retrieved successfully.", agent_unanswered_questions(agent))

    def post(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not can_manage_agent(request.user, agent):
            return error_response("You do not have permission to train this agent.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = AIAgentTrainFAQSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Training FAQ creation failed.", serializer.errors)
        faq = AIAgentFAQ.objects.create(agent=agent, is_public=True, is_active=True, **serializer.validated_data)
        return success_response("Training FAQ created successfully.", AIAgentFAQSerializer(faq).data, status.HTTP_201_CREATED)


class AIAgentSyncKnowledgeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, agent_id):
        agent = get_user_agent(request.user, agent_id)
        if not can_manage_agent(request.user, agent):
            return error_response("You do not have permission to sync this agent.", status_code=status.HTTP_403_FORBIDDEN)
        items = sync_agent_knowledge(agent)
        serializer = AIAgentKnowledgeSerializer(items, many=True, context={"request": request})
        return success_response("Knowledge synced successfully.", {"count": len(items), "items": serializer.data})
