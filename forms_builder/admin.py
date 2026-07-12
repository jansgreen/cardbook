from django.contrib import admin

from .models import FormDefinition, FormField, FormSubmission


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "recipient_email", "is_active", "updated_at")
    list_filter = ("is_active", "company")
    search_fields = ("name", "recipient_email", "company__name")
    inlines = [FormFieldInline]


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("form", "sender_name", "sender_email", "email_sent", "created_at")
    list_filter = ("email_sent", "form__company")
    search_fields = ("form__name", "form__company__name", "sender_email", "sender_name")
    readonly_fields = ("form", "data", "sender_name", "sender_email", "ip_address", "user_agent", "email_sent", "email_error", "created_at")

