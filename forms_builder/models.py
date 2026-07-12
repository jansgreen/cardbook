from django.conf import settings
from django.db import models
from django.utils.text import slugify

from companies.models import Company


def unique_form_slug(company, name, instance=None):
    base = slugify(name) or "form"
    slug = base
    counter = 1
    queryset = FormDefinition.objects.filter(company=company)
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


class FormDefinition(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="forms")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    recipient_email = models.EmailField()
    success_message = models.CharField(max_length=240, default="Gracias. Hemos recibido tu mensaje.")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_forms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "slug"], name="unique_form_slug_per_company"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_form_slug(self.company, self.name, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company} / {self.name}"


class FormField(models.Model):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    DATE = "date"

    FIELD_TYPES = [
        (TEXT, "Texto"),
        (EMAIL, "Email"),
        (PHONE, "Telefono"),
        (TEXTAREA, "Parrafo"),
        (SELECT, "Selector"),
        (CHECKBOX, "Checkbox"),
        (NUMBER, "Numero"),
        (DATE, "Fecha"),
    ]

    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=140)
    field_type = models.CharField(max_length=30, choices=FIELD_TYPES, default=TEXT)
    placeholder = models.CharField(max_length=160, blank=True)
    help_text = models.CharField(max_length=180, blank=True)
    choices = models.TextField(blank=True, help_text="Una opcion por linea para campos selector.")
    is_required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def choice_list(self):
        return [item.strip() for item in self.choices.splitlines() if item.strip()]

    def __str__(self):
        return f"{self.form} / {self.label}"


class FormSubmission(models.Model):
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="submissions")
    data = models.JSONField(default=dict)
    sender_name = models.CharField(max_length=160, blank=True)
    sender_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    email_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.form} / {self.created_at:%Y-%m-%d %H:%M}"
