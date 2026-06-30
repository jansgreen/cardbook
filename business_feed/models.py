from django.conf import settings
from django.db import models

from companies.models import Company


class BusinessPost(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"
    MEDIA_TYPE_CHOICES = [
        (MEDIA_IMAGE, "Imagen"),
        (MEDIA_VIDEO, "Video corto"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="business_posts")
    title = models.CharField(max_length=160)
    caption = models.TextField(blank=True, null=True)
    media = models.FileField(upload_to="business_posts/")
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default=MEDIA_IMAGE)
    view_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.name} - {self.title}"


class BusinessPostExcellent(models.Model):
    post = models.ForeignKey(BusinessPost, on_delete=models.CASCADE, related_name="excellents")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_excellents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Excelente: {self.post_id} by {self.user_id}"
