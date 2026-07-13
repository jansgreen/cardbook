from django.contrib import admin

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "user", "category", "priority", "status", "created_at")
    list_filter = ("category", "priority", "status", "created_at")
    search_fields = ("subject", "message", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "technical_context")
