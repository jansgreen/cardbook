from rest_framework import serializers

from companies.serializers import CompanySerializer
from .models import CompanyAlliance


class CompanyAllianceSerializer(serializers.ModelSerializer):
    requester_detail = CompanySerializer(source="requester", read_only=True)
    receiver_detail = CompanySerializer(source="receiver", read_only=True)

    class Meta:
        model = CompanyAlliance
        fields = [
            "id",
            "requester",
            "receiver",
            "requester_detail",
            "receiver_detail",
            "requested_by",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "requested_by", "status", "created_at", "updated_at"]
