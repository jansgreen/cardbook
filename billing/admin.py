from django.contrib import admin

from .models import Invoice, Payment, Refund, StripeConfiguration, StripeEvent


@admin.register(StripeConfiguration)
class StripeConfigurationAdmin(admin.ModelAdmin):
    list_display = ("mode", "is_active", "publishable_key", "updated_at")
    list_filter = ("mode", "is_active")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("company", "invoice_number", "total", "amount_paid", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("company__name", "stripe_invoice_id", "invoice_number")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("company", "amount", "currency", "status", "stripe_fee", "net_amount", "paid_at")
    list_filter = ("status", "currency", "payment_method")
    search_fields = ("company__name", "stripe_payment_intent_id", "stripe_invoice_id")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "amount", "status", "processed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("stripe_refund_id", "payment__company__name")


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "processed_at")
    search_fields = ("event_id", "event_type")
