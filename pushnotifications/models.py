from django.conf import settings
from django.db import models


class PushDevice(models.Model):
    PLATFORM_ANDROID = "android"
    PLATFORM_IOS = "ios"
    PLATFORM_WEB = "web"

    PLATFORM_CHOICES = [
        (PLATFORM_ANDROID, "Android"),
        (PLATFORM_IOS, "iOS"),
        (PLATFORM_WEB, "Web"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_devices",
    )
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default=PLATFORM_ANDROID)
    device_id = models.CharField(max_length=160, blank=True)
    app_version = models.CharField(max_length=40, blank=True)
    enabled = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.user} {self.platform} {self.token[:12]}"


class PushDeliveryLog(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_SKIPPED = "skipped"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_SKIPPED, "Skipped"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_delivery_logs",
    )
    device = models.ForeignKey(PushDevice, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status}: {self.title}"
