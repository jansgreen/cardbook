from django.contrib import admin

from .models import Block, Component, Layout, Page, Section, Theme, Website, WebsiteClick, WebsiteVisit


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "slug", "is_published", "updated_at")
    list_filter = ("is_published", "theme")
    search_fields = ("title", "company__name", "slug", "domain", "subdomain")


admin.site.register(Page)
admin.site.register(Layout)
admin.site.register(Section)
admin.site.register(Component)
admin.site.register(Block)
admin.site.register(WebsiteVisit)
admin.site.register(WebsiteClick)
