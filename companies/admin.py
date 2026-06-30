from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "owner__username", "owner__email")
