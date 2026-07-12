from django.contrib import admin

from .models import AuditLog, RevenueSnapshot


@admin.register(RevenueSnapshot)
class RevenueSnapshotAdmin(admin.ModelAdmin):
    list_display = ("period_type", "period_start", "period_end", "gross_revenue", "net_revenue", "active_subscriptions")
    list_filter = ("period_type",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "title", "actor", "severity", "target_type", "target_id")
    list_filter = ("action", "severity", "created_at")
    search_fields = ("action", "title", "message", "actor__username", "actor__email", "target_type", "target_id")
    readonly_fields = ("created_at", "actor", "action", "severity", "target_type", "target_id", "title", "message", "metadata", "ip_address", "user_agent")
