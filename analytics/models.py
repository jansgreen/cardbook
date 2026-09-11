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
        ("contact_cta_click", "Contact CTA click"),
        ("contact_reveal", "Contact reveal"),
        ("phone_click", "Phone click"),
        ("whatsapp_click", "WhatsApp click"),
        ("email_click", "Email click"),
        ("website_click", "Website click"),
        ("quote_request", "Quote request"),
        ("appointment_request", "Appointment request"),
        ("directions_click", "Directions click"),
        ("message_click", "Message click"),
        ("social_click", "Social click"),
        ("phone", "Phone legacy"),
        ("email", "Email legacy"),
        ("website", "Website legacy"),
        ("whatsapp", "WhatsApp legacy"),
        ("social", "Social legacy"),
    ]

    card = models.ForeignKey(DigitalCard, on_delete=models.CASCADE, related_name="clicks")
    click_type = models.CharField(max_length=32, choices=CLICK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
