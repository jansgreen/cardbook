from django.contrib import admin

from .models import AgentCardSale, AgentProfile, Commission, Referral, ReferralInvitation, ReferralNotification
from .services import approve_commission, mark_commission_paid


@admin.action(description="Aprobar comisiones seleccionadas")
def approve_selected(modeladmin, request, queryset):
    for commission in queryset.filter(status=Commission.STATUS_PENDING):
        approve_commission(commission=commission, approved_by=request.user)


@admin.action(description="Marcar comisiones seleccionadas como pagadas")
def mark_paid_selected(modeladmin, request, queryset):
    for commission in queryset.exclude(status=Commission.STATUS_PAID):
        mark_commission_paid(commission=commission, paid_by=request.user)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ["agent_id", "user", "referral_code", "commission_percentage", "is_active", "approved_at", "created_at"]
    list_filter = ["is_active", "created_at", "approved_at"]
    search_fields = ["agent_id", "referral_code", "user__username", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["agent_id", "referral_code", "approved_at", "created_at"]


@admin.register(ReferralInvitation)
class ReferralInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "status", "invited_by", "created_at", "expires_at", "accepted_at"]
    list_filter = ["status", "created_at", "expires_at"]
    search_fields = ["email", "token", "invited_by__email"]
    readonly_fields = ["token", "created_at", "accepted_at"]


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ["referral_code", "agent", "referred_user", "referred_company", "ip_address", "created_at"]
    list_filter = ["created_at", "agent"]
    search_fields = ["referral_code", "agent__agent_id", "agent__referral_code", "referred_user__email", "referred_company__name"]
    readonly_fields = ["agent", "referred_user", "referred_company", "referral_code", "source_url", "ip_address", "user_agent", "created_at"]


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ["agent", "company", "plan_name", "payment_amount", "commission_amount", "currency", "status", "created_at", "paid_at"]
    list_filter = ["status", "currency", "created_at", "paid_at"]
    search_fields = ["agent__agent_id", "agent__referral_code", "company__name", "plan_name", "payment_reference"]
    readonly_fields = ["commission_amount", "created_at", "approved_at", "paid_at"]
    actions = [approve_selected, mark_paid_selected]


@admin.register(AgentCardSale)
class AgentCardSaleAdmin(admin.ModelAdmin):
    list_display = ["agent", "company", "sale_type", "gross_amount", "commission_amount", "currency", "status", "created_at"]
    list_filter = ["sale_type", "status", "currency", "created_at"]
    search_fields = ["agent__agent_id", "agent__referral_code", "company__name", "created_by__email"]
    readonly_fields = ["agent", "access_grant", "company", "created_by", "digital_card", "business_card", "commission", "created_at"]


@admin.register(ReferralNotification)
class ReferralNotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "event_type", "title", "created_at", "read_at"]
    list_filter = ["event_type", "created_at", "read_at"]
    search_fields = ["recipient__username", "recipient__email", "title", "message"]
    readonly_fields = ["created_at", "read_at"]
