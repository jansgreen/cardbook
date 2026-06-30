from django.contrib import admin

from .models import DigitalCard


@admin.register(DigitalCard)
class DigitalCardAdmin(admin.ModelAdmin):
    list_display = ("slug", "company", "user", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("slug", "company__name", "user__username")
