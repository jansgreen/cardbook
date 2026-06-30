from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Cardbook profile", {"fields": ("phone_number", "avatar", "preferred_language")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "preferred_language", "is_staff")
