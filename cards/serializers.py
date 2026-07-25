from rest_framework import serializers

from django.urls import reverse

from .models import BusinessCard, DigitalCard
from .services import (
    CARD_TYPE_BUSINESS_PRESENTATION,
    CARD_TYPE_BUSINESS_PROFILE,
    can_create_profile_for_company,
    can_use_profile_for_business_card,
)


class DigitalCardSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    card_type = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    qr_svg_url = serializers.SerializerMethodField()

    class Meta:
        model = DigitalCard
        fields = [
            "id",
            "card_type",
            "company",
            "user",
            "slug",
            "public_url",
            "qr_svg_url",
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
        if request and not can_create_profile_for_company(request.user, company):
            raise serializers.ValidationError("You do not belong to this company.")
        return company

    def get_card_type(self, obj):
        return CARD_TYPE_BUSINESS_PROFILE

    def get_public_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-card-web", kwargs={"slug": obj.slug})
        return request.build_absolute_uri(path) if request else path

    def get_qr_svg_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-card-qr", kwargs={"slug": obj.slug})
        return request.build_absolute_uri(path) if request else path


class BusinessCardSerializer(serializers.ModelSerializer):
    profile_slug = serializers.CharField(source="profile.slug", read_only=True)
    company = serializers.IntegerField(source="company.id", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)
    card_type = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    qr_svg_url = serializers.SerializerMethodField()

    class Meta:
        model = BusinessCard
        fields = [
            "id",
            "card_type",
            "profile",
            "profile_slug",
            "public_url",
            "qr_svg_url",
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
            "physical_card_front_image",
            "physical_card_back_image",
            "is_physical_card_imported",
            "name_font",
            "name_size",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]

    def validate_profile(self, profile):
        request = self.context.get("request")
        if request and not can_use_profile_for_business_card(request.user, profile):
            raise serializers.ValidationError("You do not have permission to use this profile.")
        return profile

    def get_card_type(self, obj):
        return CARD_TYPE_BUSINESS_PRESENTATION

    def get_public_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-business-card", kwargs={"slug": obj.slug})
        return request.build_absolute_uri(path) if request else path

    def get_qr_svg_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-card-qr", kwargs={"slug": obj.profile.slug})
        return request.build_absolute_uri(path) if request else path


class PublicDigitalCardSerializer(serializers.ModelSerializer):
    translation = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    public_url = serializers.SerializerMethodField()
    qr_svg_url = serializers.SerializerMethodField()

    class Meta:
        model = DigitalCard
        fields = [
            "id",
            "company",
            "company_name",
            "user",
            "slug",
            "public_url",
            "qr_svg_url",
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

    def get_public_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-card-web", kwargs={"slug": obj.slug})
        return request.build_absolute_uri(path) if request else path

    def get_qr_svg_url(self, obj):
        request = self.context.get("request")
        path = reverse("public-card-qr", kwargs={"slug": obj.slug})
        return request.build_absolute_uri(path) if request else path
