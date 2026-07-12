from decimal import Decimal

from rest_framework import serializers

from .models import AgentProfile, Commission, Referral, ReferralInvitation, ReferralNotification
from .services import build_referral_link, generate_commission, invite_agent


class AgentProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    referral_link = serializers.SerializerMethodField()

    class Meta:
        model = AgentProfile
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "agent_id",
            "referral_code",
            "referral_link",
            "commission_percentage",
            "is_active",
            "approved_at",
            "created_at",
        ]
        read_only_fields = ["id", "agent_id", "referral_code", "approved_at", "created_at"]

    def get_referral_link(self, obj):
        request = self.context.get("request")
        return build_referral_link(request, obj) if request else ""


class AgentInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    expires_days = serializers.IntegerField(min_value=1, max_value=60, default=7)

    def create(self, validated_data):
        request = self.context["request"]
        return invite_agent(invited_by=request.user, **validated_data)


class ReferralInvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.CharField(source="invited_by.get_full_name", read_only=True)

    class Meta:
        model = ReferralInvitation
        fields = ["id", "invited_by", "invited_by_name", "email", "token", "status", "created_at", "accepted_at", "expires_at"]
        read_only_fields = ["id", "invited_by", "token", "status", "created_at", "accepted_at"]


class RegisterSourceSerializer(serializers.Serializer):
    referral_code = serializers.CharField(max_length=20)
    source_url = serializers.URLField(required=False, allow_blank=True)


class ReferralSerializer(serializers.ModelSerializer):
    agent_code = serializers.CharField(source="agent.referral_code", read_only=True)
    referred_user_email = serializers.EmailField(source="referred_user.email", read_only=True)
    referred_company_name = serializers.CharField(source="referred_company.name", read_only=True)

    class Meta:
        model = Referral
        fields = [
            "id",
            "agent",
            "agent_code",
            "referred_user",
            "referred_user_email",
            "referred_company",
            "referred_company_name",
            "referral_code",
            "source_url",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields


class CommissionSerializer(serializers.ModelSerializer):
    agent_code = serializers.CharField(source="agent.referral_code", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "agent",
            "agent_code",
            "company",
            "company_name",
            "plan_name",
            "payment_amount",
            "commission_percentage",
            "commission_amount",
            "currency",
            "payment_reference",
            "status",
            "created_at",
            "approved_at",
            "paid_at",
        ]
        read_only_fields = [
            "id",
            "agent",
            "commission_percentage",
            "commission_amount",
            "status",
            "created_at",
            "approved_at",
            "paid_at",
        ]


class GenerateCommissionSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    plan_name = serializers.CharField(max_length=120)
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_reference = serializers.CharField(max_length=180, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, default="USD")


class ReferralNotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReferralNotification
        fields = ["id", "event_type", "title", "message", "data", "is_read", "read_at", "created_at"]
        read_only_fields = fields
