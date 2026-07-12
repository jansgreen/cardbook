from rest_framework import serializers
from django.urls import reverse

from .models import CompanySpecialty, SavedJobCard, Specialty, WhiteCardJob
from .services import user_active_job_card, user_has_company


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "category", "slug", "icon", "description"]


class WhiteCardJobSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    specialty_detail = SpecialtySerializer(source="specialty", read_only=True)
    saved_total = serializers.IntegerField(source="saved_by_companies.count", read_only=True)
    public_url = serializers.SerializerMethodField()
    qr_svg_url = serializers.SerializerMethodField()

    class Meta:
        model = WhiteCardJob
        fields = [
            "id",
            "user",
            "username",
            "display_name",
            "public_url",
            "qr_svg_url",
            "title",
            "photo",
            "phone_number",
            "address",
            "linkedin_url",
            "resume_url",
            "specialty",
            "specialty_detail",
            "short_description",
            "experience",
            "languages",
            "technologies",
            "certifications",
            "availability_note",
            "quote",
            "is_active",
            "is_available",
            "card_views",
            "profile_views",
            "resume_downloads",
            "saved_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "is_active", "card_views", "profile_views", "resume_downloads", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if not self.instance and user_has_company(request.user):
            raise serializers.ValidationError("Solo usuarios sin empresa pueden crear una White Card Job.")
        if not self.instance and user_active_job_card(request.user):
            raise serializers.ValidationError("Ya tienes una White Card Job activa.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def get_public_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-white-card-job", kwargs={"username": obj.username})
        return request.build_absolute_uri(path) if request else path

    def get_qr_svg_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-white-card-job-qr", kwargs={"username": obj.username})
        return request.build_absolute_uri(path) if request else path


class CompanySpecialtySerializer(serializers.ModelSerializer):
    specialty_detail = SpecialtySerializer(source="specialty", read_only=True)

    class Meta:
        model = CompanySpecialty
        fields = ["id", "company", "specialty", "specialty_detail"]


class SavedJobCardSerializer(serializers.ModelSerializer):
    job_card_detail = WhiteCardJobSerializer(source="job_card", read_only=True)

    class Meta:
        model = SavedJobCard
        fields = ["id", "company", "job_card", "job_card_detail", "saved_by", "notes", "created_at"]
        read_only_fields = ["id", "saved_by", "created_at"]
