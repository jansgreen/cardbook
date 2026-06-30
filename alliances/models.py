from django.conf import settings
from django.db import models

from companies.models import Company


class CompanyAlliance(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_ACCEPTED, "Aceptada"),
        (STATUS_REJECTED, "Rechazada"),
    ]

    requester = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sent_alliances")
    receiver = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="received_alliances")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="requested_alliances")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("requester", "receiver")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requester_id} -> {self.receiver_id}: {self.status}"
