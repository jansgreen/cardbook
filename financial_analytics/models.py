from django.db import models

from referrals.models import AgentProfile, Commission


class ReferralClick(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="finance_referral_clicks")
    referral_code = models.CharField(max_length=80)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    landing_page = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.referral_code} - {self.agent}"


class CommissionPayment(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="finance_commission_payments")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(max_length=80, blank=True)
    transaction_reference = models.CharField(max_length=180, blank=True)
    notes = models.TextField(blank=True)
    paid_by = models.ForeignKey("accounts.Profile", on_delete=models.SET_NULL, related_name="finance_commission_payouts_made", blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    commissions = models.ManyToManyField(Commission, related_name="finance_commission_payments", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent} - {self.total_amount}"


class RevenueSnapshot(models.Model):
    PERIOD_DAILY = "daily"
    PERIOD_WEEKLY = "weekly"
    PERIOD_MONTHLY = "monthly"
    PERIOD_YEARLY = "yearly"

    PERIOD_CHOICES = [
        (PERIOD_DAILY, "Daily"),
        (PERIOD_WEEKLY, "Weekly"),
        (PERIOD_MONTHLY, "Monthly"),
        (PERIOD_YEARLY, "Yearly"),
    ]

    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stripe_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commissions_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commissions_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active_subscriptions = models.PositiveIntegerField(default=0)
    new_subscriptions = models.PositiveIntegerField(default=0)
    cancelled_subscriptions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        unique_together = ("period_type", "period_start", "period_end")

    def __str__(self):
        return f"{self.period_type}: {self.period_start} - {self.period_end}"


class AuditLog(models.Model):
    ACTION_COMMISSION_APPROVED = "commission.approved"
    ACTION_COMMISSION_PAID = "commission.paid"
    ACTION_COMMISSION_GENERATED = "commission.generated"
    ACTION_AGENT_CARD_SALE = "agent.card_sale"
    ACTION_REPORT_EXPORTED = "report.exported"
    ACTION_STRIPE_WEBHOOK = "stripe.webhook"
    ACTION_CUSTOMER_PORTAL_CREATED = "stripe.customer_portal.created"
    ACTION_REFUND_CREATED = "refund.created"
    ACTION_REFUND_FAILED = "refund.failed"
    ACTION_AGENT_PAYOUT_CREATED = "agent.payout.created"

    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_CRITICAL = "critical"

    SEVERITY_CHOICES = [
        (SEVERITY_INFO, "Info"),
        (SEVERITY_WARNING, "Warning"),
        (SEVERITY_CRITICAL, "Critical"),
    ]

    actor = models.ForeignKey("accounts.Profile", on_delete=models.SET_NULL, related_name="audit_logs", blank=True, null=True)
    action = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_INFO)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.title}"
