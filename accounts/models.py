from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Profile(AbstractUser):
    INTENT_COMPANY = "company"
    INTENT_JOB = "job"
    INTENT_AGENT = "agent"
    INTENT_CHOICES = [
        (INTENT_COMPANY, "Para mi empresa"),
        (INTENT_JOB, "Para buscar trabajo"),
        (INTENT_AGENT, "Agente de Cardbook"),
    ]

    LANGUAGE_SPANISH = "es"
    LANGUAGE_ENGLISH = "en"
    LANGUAGE_FRENCH = "fr"
    LANGUAGE_PORTUGUESE = "pt"

    LANGUAGE_CHOICES = [
        (LANGUAGE_SPANISH, "Spanish"),
        (LANGUAGE_ENGLISH, "English"),
        (LANGUAGE_FRENCH, "French"),
        (LANGUAGE_PORTUGUESE, "Portuguese"),
    ]

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_SPANISH)
    registration_intent = models.CharField(max_length=20, choices=INTENT_CHOICES, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
