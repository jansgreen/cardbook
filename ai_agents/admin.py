from django.contrib import admin

from .models import (
    AIAgent,
    AIAgentConversation,
    AIAgentFAQ,
    AIAgentKnowledgeBase,
    AIAgentLead,
    AIAgentMessage,
    AIAgentSuggestion,
)


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "agent_type", "mode", "status", "show_on_website", "updated_at")
    list_filter = ("agent_type", "mode", "status", "show_on_website", "is_active")
    search_fields = ("name", "company__name", "tone", "welcome_message")
    autocomplete_fields = ("company", "website", "created_by")


@admin.register(AIAgentKnowledgeBase)
class AIAgentKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("title", "agent", "category", "is_public", "is_active")
    list_filter = ("category", "is_public", "is_active")
    search_fields = ("title", "content", "agent__name", "agent__company__name")
    autocomplete_fields = ("agent",)


@admin.register(AIAgentFAQ)
class AIAgentFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "agent", "is_public", "is_active")
    list_filter = ("is_public", "is_active")
    search_fields = ("question", "answer", "keywords", "agent__name")
    autocomplete_fields = ("agent",)


class AIAgentMessageInline(admin.TabularInline):
    model = AIAgentMessage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(AIAgentConversation)
class AIAgentConversationAdmin(admin.ModelAdmin):
    list_display = ("agent", "company", "channel", "status", "visitor_email", "updated_at")
    list_filter = ("channel", "status")
    search_fields = ("agent__name", "company__name", "visitor_name", "visitor_email", "visitor_phone")
    autocomplete_fields = ("agent", "company", "website", "user")
    inlines = [AIAgentMessageInline]


@admin.register(AIAgentLead)
class AIAgentLeadAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "service_interest", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email", "phone", "service_interest", "message", "company__name")
    autocomplete_fields = ("agent", "company", "conversation")


@admin.register(AIAgentSuggestion)
class AIAgentSuggestionAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "agent", "priority", "is_resolved", "created_at")
    list_filter = ("priority", "is_resolved")
    search_fields = ("title", "description", "company__name", "agent__name")
    autocomplete_fields = ("agent", "company")
