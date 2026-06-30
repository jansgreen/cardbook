from rest_framework import serializers

from .models import CompanyRating


class CompanyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRating
        fields = ["id", "company", "user", "stars", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]
