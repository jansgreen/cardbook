from django.conf import settings
from django.db import models
from django.utils.text import slugify

from companies.models import Company


class NameTypographyMixin(models.Model):
    NAME_FONT_SERIF = "serif"
    NAME_FONT_SANS = "sans"
    NAME_FONT_MODERN = "modern"
    NAME_FONT_CONDENSED = "condensed"

    NAME_FONT_CHOICES = [
        (NAME_FONT_SERIF, "Editorial"),
        (NAME_FONT_SANS, "Limpia"),
        (NAME_FONT_MODERN, "Moderna"),
        (NAME_FONT_CONDENSED, "Compacta"),
    ]

    NAME_SIZE_SMALL = "small"
    NAME_SIZE_MEDIUM = "medium"
    NAME_SIZE_LARGE = "large"
    NAME_SIZE_AUTO = "auto"

    NAME_SIZE_CHOICES = [
        (NAME_SIZE_AUTO, "Automatico"),
        (NAME_SIZE_SMALL, "Pequeno"),
        (NAME_SIZE_MEDIUM, "Mediano"),
        (NAME_SIZE_LARGE, "Grande"),
    ]

    name_font = models.CharField(max_length=20, choices=NAME_FONT_CHOICES, default=NAME_FONT_SERIF)
    name_size = models.CharField(max_length=20, choices=NAME_SIZE_CHOICES, default=NAME_SIZE_AUTO)

    class Meta:
        abstract = True


class DigitalCard(NameTypographyMixin, models.Model):
    QR_SHAPE_DIAMOND = "diamond"
    QR_SHAPE_DOT = "dot"
    QR_SHAPE_SQUARE = "square"

    QR_SHAPE_CHOICES = [
        (QR_SHAPE_DIAMOND, "Diamantes"),
        (QR_SHAPE_DOT, "Puntos"),
        (QR_SHAPE_SQUARE, "Cuadros"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cards")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="digital_cards")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to="card_photos/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="card_qr/", blank=True, null=True)
    qr_shape = models.CharField(max_length=20, choices=QR_SHAPE_CHOICES, default=QR_SHAPE_DIAMOND)
    qr_dot_color = models.CharField(max_length=7, default="#003875")
    qr_background_color = models.CharField(max_length=7, default="#ffffff")
    qr_marker_color = models.CharField(max_length=7, default="#0057b8")
    whatsapp_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    x_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    infaithcore_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.user.get_full_name() or self.user.username}-{self.company.name}") or "card"
            slug = base
            counter = 1
            while DigitalCard.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug

    @property
    def user_profile_image(self):
        return self.user.avatar or self.photo


class BusinessCard(NameTypographyMixin, models.Model):
    SIZE_STANDARD = "standard"
    SIZE_CHOICES = [
        (SIZE_STANDARD, "3.5 x 2 pulgadas"),
    ]

    ORIENTATION_HORIZONTAL = "horizontal"
    ORIENTATION_VERTICAL = "vertical"
    ORIENTATION_CHOICES = [
        (ORIENTATION_HORIZONTAL, "Horizontal"),
        (ORIENTATION_VERTICAL, "Vertical"),
    ]

    profile = models.ForeignKey(DigitalCard, on_delete=models.CASCADE, related_name="business_cards")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    display_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    tagline = models.CharField(max_length=160, blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default=SIZE_STANDARD)
    orientation = models.CharField(max_length=20, choices=ORIENTATION_CHOICES, default=ORIENTATION_HORIZONTAL)
    accent_color = models.CharField(max_length=7, default="#d8a441")
    background_color = models.CharField(max_length=7, default="#003875")
    text_color = models.CharField(max_length=7, default="#ffffff")
    show_profile_photo = models.BooleanField(default=True)
    include_qr = models.BooleanField(default=True)
    hide_direct_contact_on_print = models.BooleanField(default=True)
    contact_cta_label = models.CharField(max_length=32, default="Contactanos")
    contact_cta_color = models.CharField(max_length=7, default="#003875")
    contact_cta_text_color = models.CharField(max_length=7, default="#ffffff")
    physical_card_front_image = models.ImageField(upload_to="business_cards/scans/", blank=True, null=True)
    physical_card_back_image = models.ImageField(upload_to="business_cards/scans/", blank=True, null=True)
    is_physical_card_imported = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def company(self):
        return self.profile.company

    @property
    def user(self):
        return self.profile.user

    @property
    def user_profile_image(self):
        return self.profile.user_profile_image

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.display_name}-{self.company_name}-presentacion") or "business-card"
            slug = base
            counter = 1
            while BusinessCard.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug
