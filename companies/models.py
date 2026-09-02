from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_companies")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    region = models.CharField(max_length=120, blank=True, null=True)
    show_phone = models.BooleanField(default=True)
    show_whatsapp = models.BooleanField(default=True)
    show_email = models.BooleanField(default=True)
    show_website = models.BooleanField(default=True)
    show_address = models.BooleanField(default=True)
    enable_quote_requests = models.BooleanField(default=False)
    enable_appointments = models.BooleanField(default=False)
    enable_messages = models.BooleanField(default=True)
    enable_directions = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    @property
    def efficient_count(self):
        if hasattr(self, "efficient_total"):
            return self.efficient_total or 0
        if hasattr(self, "efficient_count_value"):
            return self.efficient_count_value or 0
        return self.ratings.count()

    @property
    def efficient_badge_class(self):
        total = self.efficient_count
        if total >= 10000:
            return "gold"
        if total >= 1000:
            return "primary"
        if total >= 100:
            return "dark"
        if total >= 10:
            return "secondary"
        return "light"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "company"
            slug = base
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)
