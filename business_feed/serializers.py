from rest_framework import serializers

from .models import BusinessPost


class BusinessPostSerializer(serializers.ModelSerializer):
    excellent_count = serializers.SerializerMethodField()
    has_excellent = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)

    class Meta:
        model = BusinessPost
        fields = [
            "id",
            "company",
            "company_name",
            "company_logo",
            "title",
            "caption",
            "media",
            "media_type",
            "view_count",
            "excellent_count",
            "has_excellent",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "view_count", "is_active", "created_at"]

    def get_has_excellent(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.excellents.filter(user=request.user).exists()

    def get_excellent_count(self, obj):
        if hasattr(obj, "excellent_count"):
            return obj.excellent_count
        return obj.excellents.count()
