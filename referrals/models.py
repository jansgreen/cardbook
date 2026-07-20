import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from companies.models import Company


class AgentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile")
    agent_id = models.CharField(max_length=20, unique=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))
    is_active = models.BooleanField(default=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.agent_id:
            last_id = AgentProfile.objects.count() + 1
            candidate = f"AG-{last_id:06d}"
            while AgentProfile.objects.filter(agent_id=candidate).exclude(pk=self.pk).exists():
                last_id += 1
                candidate = f"AG-{last_id:06d}"
            self.agent_id = candidate
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        if self.is_active and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_referral_code():
        while True:
            code = f"AGT-{secrets.token_hex(3).upper()}"
            if not AgentProfile.objects.filter(referral_code=code).exists():
                return code

    def __str__(self):
        return f"{self.agent_id} - {self.user}"


class ReferralInvitation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_agent_invitations")
    email = models.EmailField()
    token = models.CharField(max_length=80, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.status == self.STATUS_PENDING and timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} ({self.status})"


class Referral(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="referrals")
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="referrals_received")
    referred_company = models.OneToOneField(Company, on_delete=models.PROTECT, related_name="referral_record", blank=True, null=True)
    referral_code = models.CharField(max_length=20)
    source_url = models.URLField(max_length=1000, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["referred_user"], name="unique_referral_per_user"),
            models.UniqueConstraint(fields=["referred_company"], name="unique_referral_per_company"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            original = Referral.objects.filter(pk=self.pk).first()
            if original:
                self.agent_id = original.agent_id
                self.referred_user_id = original.referred_user_id
                self.referral_code = original.referral_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.referral_code} -> {self.referred_user}"


class Commission(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="commissions")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="referral_commissions")
    subscription = models.ForeignKey("subscriptions.Subscription", on_delete=models.SET_NULL, related_name="referral_commissions", blank=True, null=True)
    payment = models.OneToOneField("billing.Payment", on_delete=models.PROTECT, related_name="referral_commission", blank=True, null=True)
    plan_name = models.CharField(max_length=120)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    payment_reference = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="approved_referral_commissions", blank=True, null=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="paid_referral_commissions", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_view_referrals", "Can view referrals"),
            ("can_view_commissions", "Can view commissions"),
            ("can_approve_commissions", "Can approve commissions"),
            ("can_mark_commissions_paid", "Can mark commissions paid"),
            ("can_export_financial_reports", "Can export financial reports"),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["agent", "status"]),
        ]

    def __str__(self):
        return f"{self.company} - {self.plan_name} - {self.commission_amount} {self.currency}"


class AgentCardSale(models.Model):
    SALE_TYPE_PROFILE = "business_profile"
    SALE_TYPE_PRESENTATION = "business_presentation"
    SALE_TYPE_CHOICES = [
        (SALE_TYPE_PROFILE, "Business profile"),
        (SALE_TYPE_PRESENTATION, "Business presentation card"),
    ]

    STATUS_PENDING = "pending"
    STATUS_COMMISSIONED = "commissioned"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMMISSIONED, "Commissioned"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="card_sales")
    access_grant = models.ForeignKey("accesscontrol.UserAccessGrant", on_delete=models.SET_NULL, blank=True, null=True, related_name="agent_card_sales")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="agent_card_sales")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="agent_card_sales_created")
    digital_card = models.ForeignKey("cards.DigitalCard", on_delete=models.SET_NULL, blank=True, null=True, related_name="agent_sales")
    business_card = models.ForeignKey("cards.BusinessCard", on_delete=models.SET_NULL, blank=True, null=True, related_name="agent_sales")
    commission = models.OneToOneField(Commission, on_delete=models.SET_NULL, blank=True, null=True, related_name="card_sale")
    sale_type = models.CharField(max_length=40, choices=SALE_TYPE_CHOICES)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["digital_card", "sale_type"], condition=models.Q(digital_card__isnull=False), name="unique_agent_sale_per_profile"),
            models.UniqueConstraint(fields=["business_card", "sale_type"], condition=models.Q(business_card__isnull=False), name="unique_agent_sale_per_business_card"),
        ]
        indexes = [
            models.Index(fields=["agent", "status"]),
            models.Index(fields=["company", "created_at"]),
        ]

    def __str__(self):
        return f"{self.agent.agent_id} - {self.company} - {self.sale_type}"


class ReferralNotification(models.Model):
    TYPE_REFERRAL = "referral_registered"
    TYPE_COMPANY = "company_registered"
    TYPE_COMMISSION = "commission_generated"
    TYPE_APPROVED = "commission_approved"
    TYPE_PAID = "commission_paid"
    TYPE_AGENT_SALE = "agent_card_sale"
    TYPE_FINANCE_ALERT = "finance_alert"
    TYPE_AI_LEAD = "ai_lead"
    TYPE_CHOICES = [
        (TYPE_REFERRAL, "Referral registered"),
        (TYPE_COMPANY, "Company registered"),
        (TYPE_COMMISSION, "Commission generated"),
        (TYPE_APPROVED, "Commission approved"),
        (TYPE_PAID, "Commission paid"),
        (TYPE_AGENT_SALE, "Agent card sale"),
        (TYPE_FINANCE_ALERT, "Finance alert"),
        (TYPE_AI_LEAD, "AI lead captured"),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_notifications")
    event_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "read_at", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])
        return self

    def __str__(self):
        return f"{self.recipient} - {self.title}"
