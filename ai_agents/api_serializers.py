from rest_framework import serializers

from .models import AIAgent, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead


class AIAgentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    website_title = serializers.CharField(source="website.title", read_only=True)
    agent_type_label = serializers.CharField(source="get_agent_type_display", read_only=True)
    mode_label = serializers.CharField(source="get_mode_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AIAgent
        fields = [
            "id",
            "company",
            "company_name",
            "website",
            "website_title",
            "name",
            "agent_type",
            "agent_type_label",
            "mode",
            "mode_label",
            "status",
            "status_label",
            "default_language",
            "tone",
            "welcome_message",
            "fallback_message",
            "can_capture_leads",
            "show_on_website",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "company_name",
            "website",
            "website_title",
            "agent_type",
            "agent_type_label",
            "mode",
            "mode_label",
            "created_at",
            "updated_at",
        ]

    def validate_mode(self, value):
        if value != AIAgent.MODE_RULE_BASED:
            raise serializers.ValidationError("Por ahora solo esta habilitado el modo sin costo basado en reglas.")
        return value


class AIAgentKnowledgeSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = AIAgentKnowledgeBase
        fields = [
            "id",
            "agent",
            "category",
            "category_label",
            "title",
            "content",
            "is_public",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "agent", "category_label", "created_at", "updated_at"]


class AIAgentFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAgentFAQ
        fields = [
            "id",
            "agent",
            "question",
            "answer",
            "keywords",
            "is_public",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "agent", "created_at", "updated_at"]


class AIAgentLeadSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AIAgentLead
        fields = [
            "id",
            "agent",
            "company",
            "conversation",
            "name",
            "email",
            "phone",
            "service_interest",
            "message",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "agent",
            "company",
            "conversation",
            "status_label",
            "created_at",
            "updated_at",
        ]


class AIAgentTestQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)


class AIAgentTrainFAQSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=255)
    answer = serializers.CharField()
    keywords = serializers.CharField(max_length=255, required=False, allow_blank=True)

