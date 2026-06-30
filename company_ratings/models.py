from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from companies.models import Company


class CompanyRating(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_ratings")
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "user")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.company_id}: {self.stars}"
