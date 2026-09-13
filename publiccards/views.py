import re
from urllib.parse import urlparse

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from analytics.models import CardView
from alliances.models import CompanyAlliance
from book.models import SavedBusiness
from cardbookweb.qr import qr_svg_response, static_image_data_uri, style_from_object
from cardbookweb.social import social_image_context
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from cards.permissions import can_manage_card
from websitebuilder.models import Website
from websitebuilder.services import website_public_url


LANGUAGE_OPTIONS = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("pt", "Português"),
]
BUSINESS_LABELS = {
    "es": {
        "services": "Servicios",
        "scan": "Escanea mi perfil",
        "title": "Tarjeta de presentacion",
        "description": "Formato digital con proporcion convencional, lista para compartir por enlace o escanear desde el QR.",
        "profile": "Ver perfil del negocio",
        "share": "Compartir tarjeta",
        "dashboard": "Ir a dashboard",
        "print": "Vista de impresion",
        "language": "Idioma",
    },
    "en": {
        "services": "Services",
        "scan": "Scan my profile",
        "title": "Business card",
        "description": "Digital format with a conventional business-card ratio, ready to share by link or QR.",
        "profile": "View business profile",
        "share": "Share card",
        "dashboard": "Go to dashboard",
        "print": "Print view",
        "language": "Language",
    },
    "fr": {
        "services": "Services",
        "scan": "Scanner mon profil",
        "title": "Carte de visite",
        "description": "Format numerique avec proportion conventionnelle, pret a partager par lien ou QR.",
        "profile": "Voir le profil",
        "share": "Partager",
        "dashboard": "Tableau de bord",
        "print": "Vue impression",
        "language": "Langue",
    },
    "pt": {
        "services": "Servicos",
        "scan": "Escaneie meu perfil",
        "title": "Cartao de visita",
        "description": "Formato digital com proporcao convencional, pronto para compartilhar por link ou QR.",
        "profile": "Ver perfil",
        "share": "Compartilhar",
        "dashboard": "Ir ao dashboard",
        "print": "Vista de impressao",
        "language": "Idioma",
    },
}


def card_qr_svg(request, slug):
    card = get_object_or_404(DigitalCard.objects.filter(is_active=True), slug=slug)
    card_url = request.build_absolute_uri(reverse("public-card-web", kwargs={"slug": card.slug}))
    logo_url = static_image_data_uri("img/logo.png")
    return qr_svg_response(card_url, style_from_object(card), logo_url=logo_url)


def save_to_book(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('web-login')}?next={request.POST.get('next') or request.META.get('HTTP_REFERER', '/')}")
    company = None
    digital_card = None
    business_card = None
    if request.POST.get("digital_card"):
        digital_card = get_object_or_404(DigitalCard.objects.filter(is_active=True), pk=request.POST["digital_card"])
        company = digital_card.company
    if request.POST.get("business_card"):
        business_card = get_object_or_404(BusinessCard.objects.filter(is_active=True), pk=request.POST["business_card"])
        company = business_card.company
        digital_card = digital_card or business_card.profile
    if request.POST.get("company"):
        company = get_object_or_404(Company.objects.filter(is_active=True), pk=request.POST["company"])
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("dashboard-book")
    if not company or company.owner_id == request.user.id:
        return redirect(next_url)
    item, _ = SavedBusiness.objects.get_or_create(
        user=request.user,
        company=company,
        defaults={"digital_card": digital_card, "business_card": business_card},
    )
    changed = False
    if digital_card and not item.digital_card_id:
        item.digital_card = digital_card
        changed = True
    if business_card and not item.business_card_id:
        item.business_card = business_card
        changed = True
    if changed:
        item.save()
    return redirect(next_url)


def get_allied_companies(company):
    alliances = CompanyAlliance.objects.filter(status=CompanyAlliance.STATUS_ACCEPTED).filter(
        Q(requester=company) | Q(receiver=company)
    ).select_related("requester", "receiver")
    ally_ids = []
    for alliance in alliances:
        ally_ids.append(alliance.receiver_id if alliance.requester_id == company.id else alliance.requester_id)
    return Company.objects.filter(id__in=ally_ids, is_active=True).annotate(efficient_total=Count("ratings", distinct=True))


def get_business_card_website_url(request, business_card):
    try:
        website = business_card.profile.company.builder_website
    except ObjectDoesNotExist:
        website = None

    if website and website.is_active and website.is_published:
        return website_public_url(request, website)

    for candidate_url in (business_card.website, business_card.profile.website, business_card.company.website):
        if not candidate_url:
            continue
        parsed = urlparse(candidate_url)
        path = parsed.path.strip("/")
        if path.startswith("site/"):
            website_slug = path.split("/", 2)[1] if len(path.split("/", 2)) > 1 else ""
            website_exists = Website.objects.filter(
                Q(slug=website_slug) | Q(subdomain=website_slug) | Q(company__slug=website_slug),
                is_active=True,
                is_published=True,
            ).exists()
            if website_slug and not website_exists:
                return request.build_absolute_uri(reverse("public-company-detail", kwargs={"slug": business_card.company.slug}))
        return candidate_url
    return ""


def get_business_card_service_items(business_card):
    services_text = business_card.services or business_card.company.services or ""
    raw_items = [item.strip(" -\t\r") for item in re.split(r"[\n;]+", services_text) if item.strip(" -\t\r")]
    if len(raw_items) <= 1 and "," in services_text:
        raw_items = [item.strip(" -\t\r") for item in services_text.split(",") if item.strip(" -\t\r")]
    return raw_items[:6]


class PublicCardDetailView(DetailView):
    model = DigitalCard
    template_name = "publiccards/card_detail.html"
    context_object_name = "card"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return DigitalCard.objects.filter(is_active=True).select_related("company", "user")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "es")
        card = self.object
        translation = card.translations.filter(language=lang).first() or card.translations.filter(language="es").first()
        card_name = translation.full_name if translation else card.user.get_full_name() or card.user.username
        card_description = (
            card.company.description
            or (translation.bio if translation and translation.bio else "")
            or card.job_title
            or "Perfil digital en incardbook."
        )
        context.update({
            "lang": lang,
            "translation": translation,
            "language_options": LANGUAGE_OPTIONS,
            "available_languages": card.translations.values_list("language", flat=True),
            "can_print": self.request.user.is_authenticated and can_manage_card(self.request.user, card),
            "print_business_card": card.business_cards.filter(is_active=True).first(),
            "allied_companies": get_allied_companies(card.company),
            "social_title": f"{card_name} - {card.company.name}",
            "social_description": card_description,
            **social_image_context(self.request, card.company.logo, card.user.avatar, card.photo),
        })
        return context

    def render_to_response(self, context, **response_kwargs):
        CardView.objects.create(
            card=self.object,
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
            source="web",
            language=self.request.GET.get("lang", "es"),
        )
        return super().render_to_response(context, **response_kwargs)


class PublicBusinessCardDetailView(DetailView):
    model = BusinessCard
    template_name = "publiccards/business_card_detail.html"
    context_object_name = "business_card"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return BusinessCard.objects.filter(is_active=True, profile__is_active=True).select_related(
            "profile__company",
            "profile__company__builder_website",
            "profile__user",
        )

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "es")
        if lang not in dict(LANGUAGE_OPTIONS):
            lang = "es"
        context["profile_url"] = self.request.build_absolute_uri(
            f'{reverse("public-card-web", kwargs={"slug": self.object.profile.slug})}?lang={lang}'
        )
        context["lang"] = lang
        context["labels"] = BUSINESS_LABELS.get(lang, BUSINESS_LABELS["es"])
        context["language_options"] = LANGUAGE_OPTIONS
        context["can_print"] = self.request.user.is_authenticated and can_manage_card(self.request.user, self.object.profile)
        context["allied_companies"] = get_allied_companies(self.object.company)
        context["business_website_url"] = get_business_card_website_url(self.request, self.object)
        context["social_title"] = f"{self.object.company_name} - {self.object.display_name}"
        context["social_description"] = self.object.tagline or self.object.services or self.object.company.description or "Tarjeta de presentacion comercial en incardbook."
        context.update(social_image_context(
            self.request,
            self.object.company.logo,
            self.object.profile.user.avatar,
            self.object.profile.photo,
        ))
        return context


class BusinessCardPrintView(LoginRequiredMixin, DetailView):
    login_url = "/login/"
    model = BusinessCard
    template_name = "publiccards/business_card_print.html"
    context_object_name = "business_card"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return BusinessCard.objects.filter(is_active=True, profile__is_active=True).select_related(
            "profile__company",
            "profile__company__builder_website",
            "profile__user",
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.object = self.get_object()
        if not can_manage_card(request.user, self.object.profile):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paper = self.request.GET.get("paper", "letter")
        if paper not in {"letter", "a4"}:
            paper = "letter"
        layout = self.request.GET.get("layout", "cards")
        if layout not in {"cards", "qr_double"}:
            layout = "cards"
        context.update({
            "paper": paper,
            "layout": layout,
            "paper_css": ("A4 landscape" if paper == "a4" else "letter landscape") if layout == "qr_double" else ("A4" if paper == "a4" else "letter"),
            "copies": range(10),
            "qr_copies": range(2),
            "profile_url": self.request.build_absolute_uri(
                reverse("public-card-web", kwargs={"slug": self.object.profile.slug})
            ),
            "business_website_url": get_business_card_website_url(self.request, self.object),
            "business_service_heading": self.object.company.category or "Servicios de la empresa",
            "business_service_items": get_business_card_service_items(self.object),
        })
        return context


class PublicCompanyDetailView(DetailView):
    model = Company
    template_name = "publiccards/company_detail.html"
    context_object_name = "company"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Company.objects.filter(is_active=True).annotate(efficient_total=Count("ratings", distinct=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allied_companies"] = get_allied_companies(self.object)
        context["posts"] = self.object.business_posts.filter(is_active=True)[:6]
        context["digital_cards"] = self.object.cards.filter(is_active=True)[:4]
        context["social_title"] = f"{self.object.name} - incardbook"
        context["social_description"] = self.object.description or self.object.services or "Perfil empresarial en incardbook."
        context.update(social_image_context(self.request, self.object.logo))
        return context
