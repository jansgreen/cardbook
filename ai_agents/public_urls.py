from django.urls import path

from .views import PublicAIAgentAskView


urlpatterns = [
    path("public/ask/", PublicAIAgentAskView.as_view(), name="public-ai-agent-ask"),
]
