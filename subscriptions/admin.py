from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("company", "plan", "status", "billing_interval", "unit_amount", "current_period_end")
    list_filter = ("status", "billing_interval", "plan")
    search_fields = ("company__name", "stripe_customer_id", "stripe_subscription_id")

