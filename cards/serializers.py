from rest_framework import serializers

from companies.permissions import can_access_company
from .models import BusinessCard, DigitalCard
from .permissions import can_manage_card


class DigitalCardSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DigitalCard
        fields = [
            "id",
            "company",
            "user",
            "slug",
            "job_title",
            "phone_number",
            "email",
            "website",
            "photo",
            "name_font",
            "name_size",
            "qr_code",
            "qr_shape",
            "qr_dot_color",
            "qr_marker_color",
            "qr_background_color",
            "whatsapp_url",
            "instagram_url",
            "facebook_url",
            "linkedin_url",
            "x_url",
            "youtube_url",
            "tiktok_url",
            "github_url",
            "infaithcore_url",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "slug", "qr_code", "is_active", "created_at", "updated_at"]

    def validate_company(self, company):
        request = self.context.get("request")
        if request and not can_access_company(request.user, company):
            raise serializers.ValidationError("You do not belong to this company.")
        return company


class BusinessCardSerializer(serializers.ModelSerializer):
    profile_slug = serializers.CharField(source="profile.slug", read_only=True)
    company = serializers.IntegerField(source="company.id", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)

    class Meta:
        model = BusinessCard
        fields = [
            "id",
            "profile",
            "profile_slug",
            "company",
            "company_logo",
            "slug",
            "display_name",
            "job_title",
            "company_name",
            "phone_number",
            "email",
            "website",
            "address",
            "tagline",
            "services",
            "size",
            "orientation",
            "accent_color",
            "background_color",
            "text_color",
            "include_qr",
            "name_font",
            "name_size",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]

    def validate_profile(self, profile):
        request = self.context.get("request")
        if request and not can_manage_card(request.user, profile):
            raise serializers.ValidationError("You do not have permission to use this profile.")
        return profile


class PublicDigitalCardSerializer(serializers.ModelSerializer):
    translation = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = DigitalCard
        fields = [
            "id",
            "company",
            "company_name",
            "user",
            "slug",
            "job_title",
            "phone_number",
            "email",
            "website",
            "photo",
            "name_font",
            "name_size",
            "qr_code",
            "qr_shape",
            "qr_dot_color",
            "qr_marker_color",
            "qr_background_color",
            "whatsapp_url",
            "instagram_url",
            "facebook_url",
            "linkedin_url",
            "x_url",
            "youtube_url",
            "tiktok_url",
            "github_url",
            "infaithcore_url",
            "translation",
        ]

    def get_translation(self, obj):
        language = self.context.get("language") or "es"
        translation = obj.translations.filter(language=language).first() or obj.translations.filter(language="es").first()
        if not translation:
            return None
        return {
            "language": translation.language,
            "full_name": translation.full_name,
            "bio": translation.bio,
            "services": translation.services,
            "address": translation.address,
            "custom_message": translation.custom_message,
        }
