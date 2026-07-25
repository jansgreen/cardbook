from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Cardbook profile", {"fields": ("phone_number", "avatar", "preferred_language", "registration_intent")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "preferred_language", "registration_intent", "is_staff")
    list_filter = UserAdmin.list_filter + ("registration_intent",)
