from rest_framework import serializers

from cards.serializers import PublicDigitalCardSerializer
from companies.serializers import CompanySerializer
from .models import SavedBusiness


class SavedBusinessSerializer(serializers.ModelSerializer):
    company_detail = CompanySerializer(source="company", read_only=True)
    digital_card_detail = PublicDigitalCardSerializer(source="digital_card", read_only=True)

    class Meta:
        model = SavedBusiness
        fields = [
            "id",
            "company",
            "company_detail",
            "digital_card",
            "digital_card_detail",
            "business_card",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
