from django.urls import path

from .views import DashboardAIAgentLeadsCSVView, DashboardAIAgentsView


urlpatterns = [
    path("leads.csv", DashboardAIAgentLeadsCSVView.as_view(), name="dashboard-ai-agent-leads-csv"),
    path("", DashboardAIAgentsView.as_view(), name="dashboard-ai-agents"),
]
