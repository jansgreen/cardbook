from django.db.models.signals import post_save
from django.dispatch import receiver

from companies.models import Company
from .services import attach_company_to_referral


@receiver(post_save, sender=Company)
def attach_referral_when_company_is_created(sender, instance, created, **kwargs):
    if created:
        attach_company_to_referral(user=instance.owner, company=instance)
