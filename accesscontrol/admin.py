from django.contrib import admin

from .models import AccessGroup, AccessPermission, AccessRole, UserAccessGrant


@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(AccessRole)
class AccessRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_agent_role", "default_commission_percent", "is_active")
    search_fields = ("name",)
    list_filter = ("is_agent_role", "is_active")
    filter_horizontal = ("permissions",)


@admin.register(AccessGroup)
class AccessGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    filter_horizontal = ("roles", "permissions")


@admin.register(UserAccessGrant)
class UserAccessGrantAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "group", "commission_percent", "is_active")
    search_fields = ("user__email", "user__username", "company__name", "role__name")
    list_filter = ("is_active", "role", "company")
