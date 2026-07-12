from django.db import models

from companies.models import Company


class Subscription(models.Model):
    STATUS_TRIALING = "trialing"
    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_CANCELLED = "cancelled"
    STATUS_INCOMPLETE = "incomplete"
    STATUS_UNPAID = "unpaid"
    STATUS_PAUSED = "paused"

    STATUS_CHOICES = [
        (STATUS_TRIALING, "Trialing"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past due"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_INCOMPLETE, "Incomplete"),
        (STATUS_UNPAID, "Unpaid"),
        (STATUS_PAUSED, "Paused"),
    ]

    INTERVAL_MONTHLY = "monthly"
    INTERVAL_YEARLY = "yearly"

    INTERVAL_CHOICES = [
        (INTERVAL_MONTHLY, "Monthly"),
        (INTERVAL_YEARLY, "Yearly"),
    ]

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="subscriptions")
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, unique=True)
    plan = models.CharField(max_length=80)
    unit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INCOMPLETE)
    billing_interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES, default=INTERVAL_MONTHLY)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    trial_start = models.DateTimeField(blank=True, null=True)
    trial_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        permissions = [
            ("can_view_financial_dashboard", "Can view financial dashboard"),
            ("can_view_subscriptions", "Can view subscriptions"),
            ("can_view_companies_billing", "Can view companies billing"),
            ("can_access_stripe_dashboard", "Can access Stripe dashboard"),
        ]

    def __str__(self):
        return f"{self.company} - {self.plan} ({self.status})"

    @property
    def normalized_mrr(self):
        if self.status not in {self.STATUS_ACTIVE, self.STATUS_TRIALING}:
            return 0
        if self.billing_interval == self.INTERVAL_YEARLY:
            return self.unit_amount / 12
        return self.unit_amount

