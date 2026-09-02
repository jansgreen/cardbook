from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "category", "show_phone", "show_whatsapp", "enable_quote_requests", "enable_appointments", "is_active")
    list_filter = ("is_active", "show_phone", "show_whatsapp", "enable_quote_requests", "enable_appointments")
    search_fields = ("name", "owner__username", "owner__email", "category", "city")
    fieldsets = (
        (None, {"fields": ("owner", "name", "slug", "logo", "description", "category", "services", "is_active")}),
        ("Contacto", {"fields": ("address", "phone_number", "email", "website", "city", "region")}),
        (
            "Ajustes de contacto publico",
            {
                "fields": (
                    "show_phone",
                    "show_whatsapp",
                    "show_email",
                    "show_website",
                    "show_address",
                    "enable_quote_requests",
                    "enable_appointments",
                    "enable_messages",
                    "enable_directions",
                )
            },
        ),
    )
    readonly_fields = ("slug",)
