from django.contrib.auth import get_user_model
from django.urls import reverse

from accesscontrol.models import UserAccessGrant
from memberships.models import CompanyMember
from referrals.models import ReferralNotification
from referrals.services import create_referral_notification


def ai_lead_notification_recipients(company):
    if not company:
        return get_user_model().objects.none()
    user_ids = {company.owner_id}
    member_ids = CompanyMember.objects.filter(
        company=company,
        is_active=True,
        role__in=[CompanyMember.ROLE_OWNER, CompanyMember.ROLE_ADMIN, CompanyMember.ROLE_MANAGER],
    ).values_list("user_id", flat=True)
    grant_ids = UserAccessGrant.objects.filter(company=company, is_active=True).values_list("user_id", flat=True)
    user_ids.update(member_ids)
    user_ids.update(grant_ids)
    return get_user_model().objects.filter(pk__in=[user_id for user_id in user_ids if user_id], is_active=True).distinct()


def notify_ai_lead_created(lead):
    recipients = ai_lead_notification_recipients(lead.company)
    action_url = f"{reverse('dashboard-ai-agents')}?agent={lead.agent_id}#leads"
    title = "Nuevo lead del agente IA"
    contact = lead.email or lead.phone or "contacto pendiente"
    message = f"{lead.name or 'Un visitante'} dejo sus datos para {lead.company.name}. Contacto: {contact}."
    notifications = []
    for recipient in recipients:
        notification = create_referral_notification(
            recipient=recipient,
            event_type=ReferralNotification.TYPE_AI_LEAD,
            title=title,
            message=message,
            data={
                "lead_id": lead.id,
                "agent_id": lead.agent_id,
                "company_id": lead.company_id,
                "action_url": action_url,
            },
        )
        if notification:
            notifications.append(notification)
    return notifications
