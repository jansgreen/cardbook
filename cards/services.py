from django.db.models import Q

from cards.models import BusinessCard, DigitalCard
from cards.permissions import can_manage_card
from companies.permissions import can_access_company
from accesscontrol.services import (
    PERM_CREATE_CARDBOOK_BUSINESS_CARDS,
    companies_for_profile_creation,
    user_has_access_permission,
)


CARD_TYPE_BUSINESS_PROFILE = "business_profile"
CARD_TYPE_BUSINESS_PRESENTATION = "business_presentation"

PERM_CREATE_PROFILE = "cards.create_profile"


def profile_creation_companies(user):
    return companies_for_profile_creation(user)


def can_create_profile_for_company(user, company):
    if not user or not user.is_authenticated or not company:
        return False
    if can_access_company(user, company):
        return True
    return user_has_access_permission(user, PERM_CREATE_PROFILE, company) or user_has_access_permission(
        user,
        PERM_CREATE_CARDBOOK_BUSINESS_CARDS,
        company,
    )


def can_use_profile_for_business_card(user, profile):
    if not user or not user.is_authenticated or not profile:
        return False
    if can_manage_card(user, profile):
        return True
    return profile.user_id == user.id and (
        user_has_access_permission(user, PERM_CREATE_PROFILE, profile.company)
        or user_has_access_permission(user, PERM_CREATE_CARDBOOK_BUSINESS_CARDS, profile.company)
    )


def can_manage_business_profile(user, profile):
    return can_use_profile_for_business_card(user, profile)


def visible_profiles_queryset(user):
    if not user or not user.is_authenticated:
        return DigitalCard.objects.none()
    if user.is_superuser:
        return DigitalCard.objects.filter(is_active=True)
    return DigitalCard.objects.filter(
        is_active=True,
    ).filter(
        Q(company__owner=user)
        | Q(company__members__user=user, company__members__is_active=True)
        | Q(user=user, company__in=profile_creation_companies(user))
    ).distinct().select_related("company", "user")


def usable_profiles_for_business_cards(user):
    profiles = visible_profiles_queryset(user)
    allowed_ids = [profile.id for profile in profiles if can_use_profile_for_business_card(user, profile)]
    return profiles.filter(id__in=allowed_ids)


def visible_business_cards_queryset(user):
    if not user or not user.is_authenticated:
        return BusinessCard.objects.none()
    if user.is_superuser:
        return BusinessCard.objects.filter(is_active=True).select_related("profile__company", "profile__user")
    return BusinessCard.objects.filter(
        is_active=True,
        profile__in=usable_profiles_for_business_cards(user),
    ).select_related("profile__company", "profile__user")


def card_type_for_instance(instance):
    if isinstance(instance, BusinessCard):
        return CARD_TYPE_BUSINESS_PRESENTATION
    if isinstance(instance, DigitalCard):
        return CARD_TYPE_BUSINESS_PROFILE
    return ""
