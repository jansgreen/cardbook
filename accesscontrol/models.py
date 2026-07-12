from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from companies.models import Company


class AccessPermission(models.Model):
    code = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name


class AccessRole(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(AccessPermission, blank=True, related_name="roles")
    is_agent_role = models.BooleanField(default=False)
    default_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "role"
            slug = base
            counter = 1
            while AccessRole.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AccessGroup(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    roles = models.ManyToManyField(AccessRole, blank=True, related_name="groups")
    permissions = models.ManyToManyField(AccessPermission, blank=True, related_name="groups")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "group"
            slug = base
            counter = 1
            while AccessGroup.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserAccessGrant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_grants")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="access_grants")
    role = models.ForeignKey(AccessRole, on_delete=models.PROTECT, related_name="grants")
    group = models.ForeignKey(AccessGroup, on_delete=models.SET_NULL, blank=True, null=True, related_name="grants")
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company__name", "user__email", "role__name"]
        unique_together = ("user", "company", "role")

    def __str__(self):
        return f"{self.user} - {self.company} - {self.role}"
