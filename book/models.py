from django.conf import settings
from django.db import models

from cards.models import BusinessCard, DigitalCard
from companies.models import Company


class SavedBusiness(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_items")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="saved_in_books")
    digital_card = models.ForeignKey(DigitalCard, on_delete=models.SET_NULL, blank=True, null=True, related_name="saved_in_books")
    business_card = models.ForeignKey(BusinessCard, on_delete=models.SET_NULL, blank=True, null=True, related_name="saved_in_books")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "company")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} saved {self.company_id}"
