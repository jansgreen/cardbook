from django.urls import path

from .api_views import (
    AIAgentAnalyticsAPIView,
    AIAgentDetailView,
    AIAgentFAQDetailAPIView,
    AIAgentFAQListCreateAPIView,
    AIAgentKnowledgeDetailAPIView,
    AIAgentKnowledgeListCreateAPIView,
    AIAgentLeadDetailAPIView,
    AIAgentLeadsAPIView,
    AIAgentListView,
    AIAgentSyncKnowledgeAPIView,
    AIAgentTestAPIView,
    AIAgentTrainingGapsAPIView,
)


urlpatterns = [
    path("", AIAgentListView.as_view(), name="api-ai-agent-list"),
    path("<int:agent_id>/", AIAgentDetailView.as_view(), name="api-ai-agent-detail"),
    path("<int:agent_id>/analytics/", AIAgentAnalyticsAPIView.as_view(), name="api-ai-agent-analytics"),
    path("<int:agent_id>/test/", AIAgentTestAPIView.as_view(), name="api-ai-agent-test"),
    path("<int:agent_id>/sync-knowledge/", AIAgentSyncKnowledgeAPIView.as_view(), name="api-ai-agent-sync-knowledge"),
    path("<int:agent_id>/knowledge/", AIAgentKnowledgeListCreateAPIView.as_view(), name="api-ai-agent-knowledge"),
    path("<int:agent_id>/knowledge/<int:item_id>/", AIAgentKnowledgeDetailAPIView.as_view(), name="api-ai-agent-knowledge-detail"),
    path("<int:agent_id>/faqs/", AIAgentFAQListCreateAPIView.as_view(), name="api-ai-agent-faqs"),
    path("<int:agent_id>/faqs/<int:faq_id>/", AIAgentFAQDetailAPIView.as_view(), name="api-ai-agent-faq-detail"),
    path("<int:agent_id>/leads/", AIAgentLeadsAPIView.as_view(), name="api-ai-agent-leads"),
    path("<int:agent_id>/leads/<int:lead_id>/", AIAgentLeadDetailAPIView.as_view(), name="api-ai-agent-lead-detail"),
    path("<int:agent_id>/training-gaps/", AIAgentTrainingGapsAPIView.as_view(), name="api-ai-agent-training-gaps"),
]

