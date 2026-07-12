from django.db.models import Count, F, Q

from companies.models import Company
from companies.permissions import can_manage_company
from .models import CompanySpecialty, SavedJobCard, Specialty, WhiteCardJob


DEFAULT_SPECIALTIES = [
    ("Plomeria", "Servicios"),
    ("Electricidad", "Servicios"),
    ("Desarrollo de Software", "Tecnologia"),
    ("Diseno Grafico", "Creatividad"),
    ("Construccion", "Servicios"),
    ("Cocina", "Hospitalidad"),
    ("Contabilidad", "Administracion"),
    ("Limpieza", "Servicios"),
    ("Soldadura", "Industria"),
    ("Mecanica", "Servicios"),
    ("Marketing", "Comercial"),
    ("Ventas", "Comercial"),
    ("Atencion al Cliente", "Comercial"),
    ("Enfermeria", "Salud"),
    ("Educacion", "Educacion"),
]


def ensure_default_specialties():
    for name, category in DEFAULT_SPECIALTIES:
        Specialty.objects.get_or_create(name=name, defaults={"category": category})


def user_has_company(user):
    return Company.objects.filter(is_active=True, owner=user).exists()


def user_active_job_card(user):
    return WhiteCardJob.objects.filter(user=user, is_active=True).select_related("specialty", "user").first()


def get_company_for_user(user, company_id=None):
    companies = (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
    ).distinct()
    if company_id:
        company = companies.filter(pk=company_id).first()
        if company:
            return company
    return companies.first()


def sync_company_specialties(company, specialty_ids):
    specialties = Specialty.objects.filter(pk__in=specialty_ids)
    CompanySpecialty.objects.filter(company=company).exclude(specialty__in=specialties).delete()
    for specialty in specialties:
        CompanySpecialty.objects.get_or_create(company=company, specialty=specialty)


def company_specialty_filter(company):
    specialty_ids = list(company.job_specialties.values_list("specialty_id", flat=True))
    filters = Q()
    if specialty_ids:
        filters |= Q(specialty_id__in=specialty_ids)
        categories = Specialty.objects.filter(pk__in=specialty_ids).values_list("category", flat=True)
        filters |= Q(specialty__category__in=[category for category in categories if category])
    if company.category:
        filters |= Q(specialty__category__icontains=company.category) | Q(specialty__name__icontains=company.category)
    if company.services:
        terms = [part.strip() for part in company.services.replace("\n", ",").split(",") if part.strip()]
        for term in terms[:5]:
            filters |= Q(specialty__name__icontains=term) | Q(short_description__icontains=term)
    return filters


def recommended_job_cards(company, limit=5):
    if not company:
        return WhiteCardJob.objects.none()
    saved_ids = SavedJobCard.objects.filter(company=company).values_list("job_card_id", flat=True)
    queryset = WhiteCardJob.objects.filter(is_active=True, is_available=True).exclude(pk__in=saved_ids).exclude(user=company.owner)
    filters = company_specialty_filter(company)
    if filters:
        queryset = queryset.filter(filters)
    if company.city:
        queryset = queryset.annotate(
            saved_total=Count("saved_by_companies", distinct=True)
        ).order_by("-updated_at", "saved_total")
        city_matches = queryset.filter(address__icontains=company.city)
        if city_matches.exists():
            queryset = city_matches
    return queryset.select_related("user", "specialty").order_by("?")[:limit]


def save_job_card_for_company(*, company, job_card, saved_by, notes=""):
    if not can_manage_company(saved_by, company):
        raise PermissionError("No puedes guardar candidatos para esta empresa.")
    if company.owner_id == job_card.user_id:
        raise ValueError("No puedes guardar tu propia tarjeta laboral.")
    item, _ = SavedJobCard.objects.get_or_create(
        company=company,
        job_card=job_card,
        defaults={"saved_by": saved_by, "notes": notes or ""},
    )
    return item


def increment_card_view(job_card, field="card_views"):
    WhiteCardJob.objects.filter(pk=job_card.pk).update(**{field: F(field) + 1})
