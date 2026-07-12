from django.conf import settings
from django.db import models
from django.utils.text import slugify

from companies.models import Company


SUPPORTED_LANGUAGES = (
    ("es", "Espanol"),
    ("en", "English"),
    ("fr", "Francais"),
    ("pt", "Portugues"),
)


def unique_slug(model, value, *, scope=None, instance=None, fallback="item"):
    base = slugify(value) or fallback
    slug = base
    counter = 1
    queryset = model.objects.all()
    if scope:
        queryset = queryset.filter(**scope)
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


class Theme(models.Model):
    BUTTON_ROUNDED = "rounded"
    BUTTON_PILL = "pill"
    BUTTON_SQUARE = "square"
    CARD_SOFT = "soft"
    CARD_BORDERED = "bordered"
    CARD_FLAT = "flat"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    preview_image = models.ImageField(upload_to="website_themes/", blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#0b5ed7")
    secondary_color = models.CharField(max_length=7, default="#083b75")
    accent_color = models.CharField(max_length=7, default="#d8a441")
    font_family = models.CharField(max_length=120, default="Inter, system-ui, sans-serif")
    button_style = models.CharField(max_length=30, default=BUTTON_PILL)
    card_style = models.CharField(max_length=30, default=CARD_SOFT)
    navbar_style = models.CharField(max_length=30, default="clean")
    footer_style = models.CharField(max_length=30, default="dark")
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Theme, self.name, instance=self, fallback="theme")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Website(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="builder_website")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    subdomain = models.SlugField(max_length=120, blank=True)
    logo = models.ImageField(upload_to="website_logos/", blank=True, null=True)
    favicon = models.ImageField(upload_to="website_favicons/", blank=True, null=True)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, blank=True, null=True, related_name="websites")
    primary_color = models.CharField(max_length=7, default="#0b5ed7")
    secondary_color = models.CharField(max_length=7, default="#083b75")
    accent_color = models.CharField(max_length=7, default="#d8a441")
    font_family = models.CharField(max_length=120, default="Inter, system-ui, sans-serif")
    show_header = models.BooleanField(default=True)
    show_nav = models.BooleanField(default=True)
    default_language = models.CharField(max_length=5, choices=SUPPORTED_LANGUAGES, default="es")
    meta_title = models.CharField(max_length=180, blank=True)
    meta_description = models.TextField(blank=True)
    custom_css = models.TextField(blank=True)
    custom_js = models.TextField(blank=True)
    custom_js_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Website, self.title or self.company.name, instance=self, fallback="site")
        if not self.subdomain:
            self.subdomain = unique_slug(Website, self.company.slug or self.company.name, instance=self, fallback="site")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Page(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, blank=True)
    icon = models.CharField(max_length=60, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_homepage = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)
    seo_title = models.CharField(max_length=180, blank=True)
    seo_description = models.TextField(blank=True)
    og_title = models.CharField(max_length=180, blank=True)
    og_image = models.ImageField(upload_to="website_og/", blank=True, null=True)
    twitter_card = models.CharField(max_length=80, default="summary_large_image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["website", "slug"], name="unique_page_slug_per_website"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Page, self.title, scope={"website": self.website}, instance=self, fallback="page")
        if self.is_homepage:
            Page.objects.filter(website=self.website, is_homepage=True).exclude(pk=self.pk).update(is_homepage=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.website} / {self.title}"


class Layout(models.Model):
    FULL_WIDTH = "full_width"
    BOXED = "boxed"
    SIDEBAR_LEFT = "sidebar_left"
    SIDEBAR_RIGHT = "sidebar_right"
    LANDING_PAGE = "landing_page"
    PORTFOLIO = "portfolio"
    BUSINESS_PROFILE = "business_profile"

    LAYOUT_CHOICES = [
        (FULL_WIDTH, "Full width"),
        (BOXED, "Boxed"),
        (SIDEBAR_LEFT, "Sidebar left"),
        (SIDEBAR_RIGHT, "Sidebar right"),
        (LANDING_PAGE, "Landing page"),
        (PORTFOLIO, "Portfolio"),
        (BUSINESS_PROFILE, "Business profile"),
    ]

    page = models.OneToOneField(Page, on_delete=models.CASCADE, related_name="layout")
    layout_type = models.CharField(max_length=40, choices=LAYOUT_CHOICES, default=FULL_WIDTH)
    name = models.CharField(max_length=120, default="Default layout")
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.page} - {self.name}"


class Section(models.Model):
    TAG_SECTION = "section"
    TAG_ARTICLE = "article"
    TAG_ASIDE = "aside"
    TAG_HEADER = "header"
    TAG_NAV = "nav"
    TAG_FOOTER = "footer"

    SECTION_TYPES = [
        ("hero", "Hero"),
        ("banner", "Banner"),
        ("services", "Services"),
        ("gallery", "Gallery"),
        ("team", "Team"),
        ("testimonials", "Testimonials"),
        ("clients", "Clients"),
        ("logos", "Logos"),
        ("cta", "CTA"),
        ("contact_form", "Contact form"),
        ("form_builder", "Forms Builder"),
        ("map", "Map"),
        ("faq", "FAQ"),
        ("footer", "Footer"),
        ("custom", "Custom"),
    ]
    HTML_TAG_CHOICES = [
        (TAG_SECTION, "section - bloque tematico"),
        (TAG_ARTICLE, "article - contenido independiente"),
        (TAG_ASIDE, "aside - contenido lateral"),
        (TAG_HEADER, "header - encabezado de seccion"),
        (TAG_NAV, "nav - navegacion secundaria"),
        (TAG_FOOTER, "footer - pie de pagina"),
    ]

    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name="sections")
    section_type = models.CharField(max_length=40, choices=SECTION_TYPES, default="custom")
    html_tag = models.CharField(max_length=20, choices=HTML_TAG_CHOICES, default=TAG_SECTION)
    name = models.CharField(max_length=120)
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.TextField(blank=True)
    background_color = models.CharField(max_length=7, blank=True)
    background_image = models.ImageField(upload_to="website_sections/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Component(models.Model):
    COMPONENT_TYPES = [
        ("service_card", "Service card"),
        ("image_card", "Image card"),
        ("testimonial_card", "Testimonial card"),
        ("team_member", "Team member"),
        ("gallery_item", "Gallery item"),
        ("faq_item", "FAQ item"),
        ("button_group", "Button group"),
        ("contact_info", "Contact info"),
        ("social_links", "Social links"),
        ("pricing_card", "Pricing card"),
        ("statistic_counter", "Statistic counter"),
        ("custom_component", "Custom component"),
    ]

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="components")
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPES, default="custom_component")
    name = models.CharField(max_length=120)
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Block(models.Model):
    BLOCK_TYPES = [
        ("text", "Text"),
        ("rich_text", "Rich text"),
        ("image", "Image"),
        ("video", "Video"),
        ("icon", "Icon"),
        ("button", "Button"),
        ("link", "Link"),
        ("phone", "Phone"),
        ("email", "Email"),
        ("address", "Address"),
        ("map", "Map"),
        ("embed", "Embed"),
        ("social_url", "Social URL"),
        ("custom", "Custom"),
    ]

    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=40, choices=BLOCK_TYPES, default="text")
    key = models.CharField(max_length=80)
    value = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="website_blocks/", blank=True, null=True)
    video = models.FileField(upload_to="website_videos/", blank=True, null=True)
    icon = models.CharField(max_length=80, blank=True)
    url = models.URLField(blank=True)
    button_text = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.component} / {self.key}"


class TranslationBase(models.Model):
    language = models.CharField(max_length=5, choices=SUPPORTED_LANGUAGES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PageTranslation(TranslationBase):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="translations")
    title = models.CharField(max_length=180, blank=True)
    seo_title = models.CharField(max_length=180, blank=True)
    seo_description = models.TextField(blank=True)

    class Meta:
        unique_together = ("page", "language")


class SectionTranslation(TranslationBase):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="translations")
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.TextField(blank=True)

    class Meta:
        unique_together = ("section", "language")


class ComponentTranslation(TranslationBase):
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name="translations")
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.TextField(blank=True)

    class Meta:
        unique_together = ("component", "language")


class BlockTranslation(TranslationBase):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="translations")
    value = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    button_text = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("block", "language")


class WebsiteVisit(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="visits")
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, blank=True, null=True, related_name="visits")
    language = models.CharField(max_length=5, default="es")
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    device = models.CharField(max_length=80, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class WebsiteClick(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="clicks")
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, blank=True, null=True, related_name="clicks")
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, blank=True, null=True, related_name="clicks")
    click_type = models.CharField(max_length=60, default="button")
    url = models.URLField(blank=True)
    language = models.CharField(max_length=5, default="es")
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
