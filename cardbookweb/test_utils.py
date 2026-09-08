from django.contrib.auth import get_user_model

from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from jobcards.models import Specialty, WhiteCardJob
from websitebuilder.services import create_starter_website


def make_user(username="user", **extra):
    defaults = {
        "email": f"{username}@incardbook.test",
        "password": "StrongPassword123!",
    }
    defaults.update(extra)
    password = defaults.pop("password")
    return get_user_model().objects.create_user(username=username, password=password, **defaults)


def make_company(owner=None, name="Cardbook Test Co", **extra):
    owner = owner or make_user("owner")
    defaults = {
        "description": "Empresa de prueba para Cardbook.",
        "category": "Tecnologia",
        "services": "Tarjetas digitales, QR, websites",
        "city": "Santo Domingo",
        "region": "DN",
        "website": "https://incardbook.test",
        "email": "hello@incardbook.test",
        "phone_number": "+18095550100",
    }
    defaults.update(extra)
    return Company.objects.create(owner=owner, name=name, **defaults)


def make_digital_card(user=None, company=None, **extra):
    user = user or make_user("carduser")
    company = company or make_company(owner=user)
    defaults = {
        "job_title": "Founder",
        "phone_number": "+18095550100",
        "email": "card@incardbook.test",
        "website": "https://incardbook.test/card",
    }
    defaults.update(extra)
    return DigitalCard.objects.create(user=user, company=company, **defaults)


def make_business_card(profile=None, **extra):
    profile = profile or make_digital_card()
    defaults = {
        "display_name": profile.user.get_full_name() or profile.user.username,
        "job_title": profile.job_title,
        "company_name": profile.company.name,
        "phone_number": profile.phone_number,
        "email": profile.email,
        "website": profile.website,
        "services": "Consultoria digital",
        "include_qr": True,
    }
    defaults.update(extra)
    return BusinessCard.objects.create(profile=profile, **defaults)


def make_white_card_job(user=None, **extra):
    user = user or make_user("jobseeker")
    specialty, _ = Specialty.objects.get_or_create(
        name=extra.pop("specialty_name", "Desarrollador Web"),
        defaults={"category": extra.pop("category", "Tecnologia")},
    )
    defaults = {
        "specialty": specialty,
        "title": "Busco Trabajo",
        "short_description": "Profesional disponible para proyectos digitales.",
        "address": "Santo Domingo",
        "is_available": True,
    }
    defaults.update(extra)
    return WhiteCardJob.objects.create(user=user, **defaults)


def make_published_website(company=None):
    company = company or make_company()
    website = create_starter_website(company, publish=True)
    website.is_published = True
    website.save(update_fields=["is_published", "updated_at"])
    website.pages.update(is_published=True)
    return website
