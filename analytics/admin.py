from django.contrib import admin

from .models import CardClick, CardView


@admin.register(CardView)
class CardViewAdmin(admin.ModelAdmin):
    list_display = ("card", "ip_address", "source", "language", "created_at")
    list_filter = ("source", "language")
    search_fields = ("card__slug", "ip_address")


@admin.register(CardClick)
class CardClickAdmin(admin.ModelAdmin):
    list_display = ("card", "click_type", "created_at")
    list_filter = ("click_type",)
    search_fields = ("card__slug",)
