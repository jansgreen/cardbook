from rest_framework import serializers

from .models import SupportTicket


class SupportTicketSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "category",
            "category_label",
            "priority",
            "priority_label",
            "status",
            "status_label",
            "subject",
            "message",
            "technical_context",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate_subject(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("El asunto debe tener al menos 5 caracteres.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 15:
            raise serializers.ValidationError("El mensaje debe tener al menos 15 caracteres.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        return SupportTicket.objects.create(user=request.user, **validated_data)
