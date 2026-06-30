from rest_framework import serializers

from .models import CardTranslation


class CardTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardTranslation
        fields = ["id", "card", "language", "full_name", "bio", "services", "address", "custom_message"]
        read_only_fields = ["id", "card"]
