from django.db import models

from companies.models import Company
from subscriptions.models import Subscription


class StripeConfiguration(models.Model):
    MODE_TEST = "test"
    MODE_LIVE = "live"
    MODE_CHOICES = [
        (MODE_TEST, "Prueba"),
        (MODE_LIVE, "Produccion"),
    ]

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, unique=True, default=MODE_TEST)
    is_active = models.BooleanField(default=True)
    publishable_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    starter_price_id = models.CharField(max_length=255, blank=True)
    business_price_id = models.CharField(max_length=255, blank=True)
    team_price_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["mode"]

    def __str__(self):
        return f"Stripe {self.get_mode_display()}"

    @property
    def dashboard_url(self):
        if self.mode == self.MODE_TEST:
            return "https://dashboard.stripe.com/test/dashboard"
        return "https://dashboard.stripe.com/dashboard"

    @property
    def masked_secret_key(self):
        if not self.secret_key:
            return ""
        return f"{self.secret_key[:7]}...{self.secret_key[-4:]}"

    @property
    def masked_webhook_secret(self):
        if not self.webhook_secret:
            return ""
        return f"{self.webhook_secret[:8]}...{self.webhook_secret[-4:]}"

    def price_id_for_plan(self, plan):
        return {
            "starter": self.starter_price_id,
            "business": self.business_price_id,
            "team": self.team_price_id,
        }.get(plan, "")

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).order_by("mode").first()


class Invoice(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_PAID = "paid"
    STATUS_VOID = "void"
    STATUS_UNCOLLECTIBLE = "uncollectible"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_PAID, "Paid"),
        (STATUS_VOID, "Void"),
        (STATUS_UNCOLLECTIBLE, "Uncollectible"),
    ]

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="invoices")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, related_name="invoices", blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    invoice_number = models.CharField(max_length=120, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    hosted_invoice_url = models.URLField(blank=True)
    invoice_pdf = models.URLField(blank=True)
    due_date = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [("can_view_payments", "Can view payments")]

    def __str__(self):
        return self.invoice_number or self.stripe_invoice_id


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_PARTIALLY_REFUNDED = "partially_refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_PARTIALLY_REFUNDED, "Partially refunded"),
    ]

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="payments")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, related_name="payments", blank=True, null=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, related_name="payments", blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=80, blank=True)
    stripe_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_view_revenue", "Can view revenue"),
            ("can_process_refunds", "Can process refunds"),
        ]

    def __str__(self):
        return f"{self.company} - {self.amount} {self.currency}"


class Refund(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    stripe_refund_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    processed_by = models.ForeignKey("accounts.Profile", on_delete=models.SET_NULL, related_name="processed_refunds", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.amount} for {self.payment_id}"


class StripeEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-processed_at"]
