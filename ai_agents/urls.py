from django.urls import path

from .views import DashboardAIAgentsView


urlpatterns = [
    path("", DashboardAIAgentsView.as_view(), name="dashboard-ai-agents"),
]
