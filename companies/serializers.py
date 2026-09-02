from rest_framework import serializers
from django.db.models import Count

from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    rating_average = serializers.SerializerMethodField()
    rating_total = serializers.SerializerMethodField()
    efficient_count = serializers.SerializerMethodField()
    efficient_badge = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "owner",
            "name",
            "slug",
            "logo",
            "address",
            "phone_number",
            "email",
            "website",
            "description",
            "category",
            "services",
            "city",
            "region",
            "show_phone",
            "show_whatsapp",
            "show_email",
            "show_website",
            "show_address",
            "enable_quote_requests",
            "enable_appointments",
            "enable_messages",
            "enable_directions",
            "rating_average",
            "rating_total",
            "efficient_count",
            "efficient_badge",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "slug", "is_active", "created_at", "updated_at"]

    def get_rating_average(self, obj):
        return self.get_efficient_count(obj)

    def get_rating_total(self, obj):
        return self.get_efficient_count(obj)

    def get_efficient_count(self, obj):
        if hasattr(obj, "efficient_total"):
            return obj.efficient_total or 0
        if hasattr(obj, "rating_total"):
            return obj.rating_total or 0
        return obj.ratings.aggregate(total=Count("id"))["total"]

    def get_efficient_badge(self, obj):
        return obj.efficient_badge_class
