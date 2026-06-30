from django.db import models

from cards.models import DigitalCard


class CardView(models.Model):
    card = models.ForeignKey(DigitalCard, on_delete=models.CASCADE, related_name="views")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CardClick(models.Model):
    CLICK_CHOICES = [
        ("phone", "Phone"),
        ("email", "Email"),
        ("website", "Website"),
        ("whatsapp", "WhatsApp"),
        ("social", "Social"),
    ]

    card = models.ForeignKey(DigitalCard, on_delete=models.CASCADE, related_name="clicks")
    click_type = models.CharField(max_length=20, choices=CLICK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
