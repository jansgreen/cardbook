from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        ACCOUNT = "account", "Account"
        MOBILE = "mobile", "Mobile app"
        BILLING = "billing", "Billing"
        COMPANIES = "companies", "Companies"
        CARDS = "cards", "Cards"
        BOOK = "book", "Book"
        ALLIANCES = "alliances", "Alliances"
        WEBSITE = "website", "Website builder"
        OTHER = "other", "Other"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    subject = models.CharField(max_length=160)
    message = models.TextField()
    technical_context = models.JSONField(default=dict, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.subject}"
