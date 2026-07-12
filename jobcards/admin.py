from django.contrib import admin

from .models import CompanySpecialty, SavedJobCard, Specialty, WhiteCardJob


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug")
    list_filter = ("category",)
    search_fields = ("name", "category", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CompanySpecialty)
class CompanySpecialtyAdmin(admin.ModelAdmin):
    list_display = ("company", "specialty")
    list_filter = ("specialty",)
    search_fields = ("company__name", "specialty__name")


@admin.register(WhiteCardJob)
class WhiteCardJobAdmin(admin.ModelAdmin):
    list_display = ("display_name", "specialty", "is_available", "is_active", "card_views", "profile_views", "created_at")
    list_filter = ("is_active", "is_available", "specialty__category", "specialty")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone_number", "address", "short_description")
    actions = ("activate_cards", "deactivate_cards", "mark_available", "mark_unavailable")

    @admin.action(description="Activar tarjetas seleccionadas")
    def activate_cards(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desactivar tarjetas seleccionadas")
    def deactivate_cards(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Marcar disponible")
    def mark_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description="Marcar no disponible")
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)


@admin.register(SavedJobCard)
class SavedJobCardAdmin(admin.ModelAdmin):
    list_display = ("company", "job_card", "saved_by", "created_at")
    list_filter = ("company", "job_card__specialty")
    search_fields = ("company__name", "job_card__user__username", "job_card__user__first_name", "job_card__user__last_name")
