from django.contrib import admin

from .models import PushDeliveryLog, PushDevice


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "platform", "enabled", "app_version", "last_seen_at")
    list_filter = ("platform", "enabled", "created_at")
    search_fields = ("user__username", "user__email", "token", "device_id")
    readonly_fields = ("created_at", "last_seen_at")


@admin.register(PushDeliveryLog)
class PushDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "title", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "title", "body", "provider_response")
    readonly_fields = ("created_at",)
