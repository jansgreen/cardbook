from django.db import models

from cards.models import DigitalCard


class CardTranslation(models.Model):
    LANGUAGE_CHOICES = [
        ("es", "Spanish"),
        ("en", "English"),
        ("fr", "French"),
        ("pt", "Portuguese"),
    ]

    card = models.ForeignKey(DigitalCard, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="es")
    full_name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    custom_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["card", "language"]
        unique_together = ("card", "language")

    def __str__(self):
        return f"{self.card.slug} ({self.language})"
