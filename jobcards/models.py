from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from companies.models import Company


class Specialty(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    icon = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name_plural = "specialties"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "specialty"
            slug = base
            counter = 1
            while Specialty.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)


class CompanySpecialty(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="job_specialties")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name="companies")

    class Meta:
        unique_together = ("company", "specialty")
        ordering = ["company__name", "specialty__name"]

    def __str__(self):
        return f"{self.company} - {self.specialty}"


class WhiteCardJob(models.Model):
    DEFAULT_TITLE = "Busco Trabajo"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="white_card_jobs")
    title = models.CharField(max_length=80, default=DEFAULT_TITLE)
    photo = models.ImageField(upload_to="jobcards/photos/", blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=180, blank=True)
    linkedin_url = models.URLField(blank=True)
    resume_url = models.URLField(blank=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name="job_cards")
    short_description = models.TextField(max_length=420)
    experience = models.CharField(max_length=80, blank=True)
    languages = models.CharField(max_length=160, blank=True)
    technologies = models.CharField(max_length=220, blank=True)
    certifications = models.CharField(max_length=220, blank=True)
    availability_note = models.CharField(max_length=120, blank=True, default="Tiempo completo")
    quote = models.CharField(max_length=220, blank=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    card_views = models.PositiveIntegerField(default=0)
    profile_views = models.PositiveIntegerField(default=0)
    resume_downloads = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="unique_active_white_card_job_per_user",
            )
        ]

    def __str__(self):
        return f"{self.display_name} - {self.specialty}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def username(self):
        return self.user.username

    @property
    def city(self):
        return (self.address or "").split(",")[0].strip()


class SavedJobCard(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="saved_job_cards")
    job_card = models.ForeignKey(WhiteCardJob, on_delete=models.CASCADE, related_name="saved_by_companies")
    saved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_job_cards")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("company", "job_card")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} saved {self.job_card}"
