from django.contrib import admin

from .models import CardTranslation


@admin.register(CardTranslation)
class CardTranslationAdmin(admin.ModelAdmin):
    list_display = ("card", "language", "full_name")
    list_filter = ("language",)
    search_fields = ("card__slug", "full_name")
