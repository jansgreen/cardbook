from django.contrib import admin

from .models import CompanyMember


@admin.register(CompanyMember)
class CompanyMemberAdmin(admin.ModelAdmin):
    list_display = ("company", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("company__name", "user__username", "user__email")
