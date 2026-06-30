from rest_framework import serializers

from .models import CardClick, CardView


class CardViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardView
        fields = ["id", "card", "ip_address", "user_agent", "source", "language", "created_at"]
        read_only_fields = ["id", "card", "ip_address", "user_agent", "created_at"]


class CardClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardClick
        fields = ["id", "card", "click_type", "created_at"]
        read_only_fields = ["id", "card", "created_at"]
