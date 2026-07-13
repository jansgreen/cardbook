import csv
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone

from accesscontrol.services import PERM_CREATE_CARDBOOK_BUSINESS_CARDS
from companies.models import Company
from financial_analytics.models import AuditLog
from financial_analytics.services import create_audit_log
from pushnotifications.services import send_push_to_user
from .models import AgentCardSale, AgentProfile, Commission, Referral, ReferralInvitation, ReferralNotification


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_referral_notification(*, recipient, event_type, title, message="", data=None):
    if not recipient:
        return None
    notification = ReferralNotification.objects.create(
        recipient=recipient,
        event_type=event_type,
        title=title,
        message=message,
        data=data or {},
    )
    send_push_to_user(
        user=recipient,
        title=title,
        body=message,
        data={"event_type": event_type, "notification_id": notification.id, **(data or {})},
    )
    return notification


def finance_notification_recipients():
    User = get_user_model()
    return User.objects.filter(is_active=True).filter(
        models.Q(is_staff=True)
        | models.Q(is_superuser=True)
        | models.Q(user_permissions__codename="can_view_financial_dashboard")
        | models.Q(groups__permissions__codename="can_view_financial_dashboard")
    ).distinct()


def notify_finance_admins(*, title, message="", data=None, exclude_user=None):
    recipients = finance_notification_recipients()
    if exclude_user:
        recipients = recipients.exclude(pk=exclude_user.pk)
    notifications = [
        ReferralNotification(
            recipient=user,
            event_type=ReferralNotification.TYPE_FINANCE_ALERT,
            title=title,
            message=message,
            data=data or {},
        )
        for user in recipients
    ]
    if notifications:
        ReferralNotification.objects.bulk_create(notifications)
    return notifications


def user_notifications(user, limit=12):
    if not user or not user.is_authenticated:
        return ReferralNotification.objects.none()
    return ReferralNotification.objects.filter(recipient=user).order_by("-created_at")[:limit]


def unread_notification_count(user):
    if not user or not user.is_authenticated:
        return 0
    return ReferralNotification.objects.filter(recipient=user, read_at__isnull=True).count()


def mark_user_notifications_read(user, notification_id=None):
    if not user or not user.is_authenticated:
        return 0
    queryset = ReferralNotification.objects.filter(recipient=user, read_at__isnull=True)
    if notification_id:
        queryset = queryset.filter(pk=notification_id)
    return queryset.update(read_at=timezone.now())


def build_referral_link(request, agent):
    path = reverse("web-register")
    url = request.build_absolute_uri(path)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}ref={agent.referral_code}"


def invite_agent(*, invited_by, email, expires_days=7):
    invitation = ReferralInvitation.objects.create(
        invited_by=invited_by,
        email=email,
        expires_at=timezone.now() + timezone.timedelta(days=expires_days),
    )
    create_referral_notification(
        recipient=invited_by,
        event_type=ReferralNotification.TYPE_REFERRAL,
        title="Invitacion de agente creada",
        message=f"Se envio una invitacion para {email}.",
        data={"invitation_id": invitation.id},
    )
    return invitation


@transaction.atomic
def accept_invitation(*, invitation, user, commission_percentage=None):
    if invitation.is_expired:
        invitation.status = ReferralInvitation.STATUS_EXPIRED
        invitation.save(update_fields=["status"])
        raise ValueError("Invitation expired.")
    if invitation.status != ReferralInvitation.STATUS_PENDING:
        raise ValueError("Invitation is not pending.")
    percentage = commission_percentage if commission_percentage is not None else Decimal("20.00")
    agent, _ = AgentProfile.objects.get_or_create(
        user=user,
        defaults={"commission_percentage": percentage, "is_active": True},
    )
    invitation.status = ReferralInvitation.STATUS_ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["status", "accepted_at"])
    return agent


def get_agent_by_code(referral_code):
    if not referral_code:
        return None
    return AgentProfile.objects.filter(referral_code__iexact=referral_code.strip(), is_active=True).select_related("user").first()


@transaction.atomic
def register_referral_source(*, user, referral_code, request=None, source_url=""):
    agent = get_agent_by_code(referral_code)
    if not agent:
        raise ValueError("Referral code is invalid or inactive.")
    if agent.user_id == user.id:
        raise ValueError("An agent cannot refer themselves.")
    referral, created = Referral.objects.get_or_create(
        referred_user=user,
        defaults={
            "agent": agent,
            "referral_code": agent.referral_code,
            "source_url": source_url or (request.build_absolute_uri() if request else ""),
            "ip_address": get_client_ip(request) if request else None,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:2000] if request else "",
        },
    )
    if created:
        create_referral_notification(
            recipient=agent.user,
            event_type=ReferralNotification.TYPE_REFERRAL,
            title="Nuevo referido registrado",
            message=f"{user.get_full_name() or user.username} se registro usando tu codigo.",
            data={"referral_id": referral.id, "user_id": user.id},
        )
    return referral


@transaction.atomic
def attach_company_to_referral(*, user, company):
    if hasattr(company, "referral_record"):
        return company.referral_record
    referral = Referral.objects.filter(referred_user=user, referred_company__isnull=True).select_related("agent").first()
    if not referral:
        return None
    referral.referred_company = company
    referral.save(update_fields=["referred_company"])
    create_referral_notification(
        recipient=referral.agent.user,
        event_type=ReferralNotification.TYPE_COMPANY,
        title="Empresa referida creada",
        message=f"{company.name} quedo asociada a tu referido.",
        data={"referral_id": referral.id, "company_id": company.id},
    )
    return referral


def calculate_commission_amount(payment_amount, commission_percentage):
    amount = Decimal(str(payment_amount))
    percentage = Decimal(str(commission_percentage))
    return (amount * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_setting(name, default):
    return Decimal(str(getattr(settings, name, default)))


def active_agent_grant_for_user(user, company=None):
    if not user or not user.is_authenticated:
        return None
    grants = user.access_grants.filter(
        is_active=True,
        role__is_active=True,
        role__is_agent_role=True,
    ).select_related("company", "role")
    if company:
        grants = grants.filter(company=company)
    return grants.order_by("-updated_at", "-created_at").first()


def ensure_agent_profile_for_grant(grant):
    if not grant:
        return None
    percentage = grant.commission_percent or grant.role.default_commission_percent or Decimal("0.00")
    agent, created = AgentProfile.objects.get_or_create(
        user=grant.user,
        defaults={
            "commission_percentage": percentage,
            "is_active": True,
        },
    )
    if not created and agent.commission_percentage != percentage:
        agent.commission_percentage = percentage
        agent.is_active = True
        agent.save(update_fields=["commission_percentage", "is_active", "approved_at"])
    return agent


def sale_amount_for_type(sale_type):
    if sale_type == AgentCardSale.SALE_TYPE_PRESENTATION:
        return _decimal_setting("CARDBOOK_AGENT_BUSINESS_CARD_SALE_AMOUNT", "25.00")
    return _decimal_setting("CARDBOOK_AGENT_PROFILE_SALE_AMOUNT", "15.00")


@transaction.atomic
def record_agent_card_sale(*, user, digital_card=None, business_card=None):
    card = business_card or digital_card
    if not card:
        return None
    company = business_card.company if business_card else digital_card.company
    sale_type = AgentCardSale.SALE_TYPE_PRESENTATION if business_card else AgentCardSale.SALE_TYPE_PROFILE
    grant = active_agent_grant_for_user(user, company)
    if not grant:
        grant = active_agent_grant_for_user(user)
    if not grant:
        return None
    if not grant.role.permissions.filter(code=PERM_CREATE_CARDBOOK_BUSINESS_CARDS, is_active=True).exists():
        return None
    agent = ensure_agent_profile_for_grant(grant)
    if not agent or not agent.is_active:
        return None

    lookup = {"business_card": business_card, "sale_type": sale_type} if business_card else {"digital_card": digital_card, "sale_type": sale_type}
    if AgentCardSale.objects.filter(**lookup).exists():
        return AgentCardSale.objects.filter(**lookup).first()

    gross_amount = sale_amount_for_type(sale_type)
    percentage = grant.commission_percent or agent.commission_percentage
    commission_amount = calculate_commission_amount(gross_amount, percentage)
    sale = AgentCardSale.objects.create(
        agent=agent,
        access_grant=grant,
        company=company,
        created_by=user,
        digital_card=digital_card,
        business_card=business_card,
        sale_type=sale_type,
        gross_amount=gross_amount,
        commission_percentage=percentage,
        commission_amount=commission_amount,
        currency=getattr(settings, "CARDBOOK_AGENT_COMMISSION_CURRENCY", "USD"),
        status=AgentCardSale.STATUS_PENDING,
        notes="Comision estimada por creacion de tarjeta mediante agente Cardbook.",
    )
    commission = Commission.objects.create(
        agent=agent,
        company=company,
        plan_name="Perfil de negocio" if sale_type == AgentCardSale.SALE_TYPE_PROFILE else "Tarjeta de presentacion",
        payment_amount=gross_amount,
        commission_percentage=percentage,
        commission_amount=commission_amount,
        currency=sale.currency,
        payment_reference=f"agent-card-sale:{sale.id}",
        status=Commission.STATUS_PENDING,
    )
    sale.commission = commission
    sale.status = AgentCardSale.STATUS_COMMISSIONED
    sale.save(update_fields=["commission", "status"])
    create_referral_notification(
        recipient=agent.user,
        event_type=ReferralNotification.TYPE_AGENT_SALE,
        title="Tarjeta creada por agente",
        message=f"Se registro una venta con comision pendiente por {company.name}.",
        data={
            "sale_id": sale.id,
            "commission_id": commission.id,
            "sale_type": sale.sale_type,
            "company_id": company.id,
        },
    )
    notify_finance_admins(
        title="Nueva comision de agente",
        message=f"{agent.user.get_full_name() or agent.user.username} genero una comision por {company.name}.",
        data={
            "sale_id": sale.id,
            "commission_id": commission.id,
            "agent_id": agent.id,
            "company_id": company.id,
            "amount": str(sale.commission_amount),
        },
        exclude_user=user,
    )
    create_audit_log(
        action=AuditLog.ACTION_AGENT_CARD_SALE,
        title="Venta de tarjeta registrada",
        actor=user,
        target=sale,
        message=f"Agente {agent.agent_id} creo una tarjeta para {company.name}.",
        metadata={
            "sale_id": sale.id,
            "sale_type": sale.sale_type,
            "commission_id": commission.id,
            "agent_id": agent.id,
            "company_id": company.id,
            "amount": str(sale.commission_amount),
        },
    )
    return sale


@transaction.atomic
def generate_commission(*, company, plan_name, payment_amount, payment_reference="", currency="USD"):
    referral = getattr(company, "referral_record", None)
    if not referral or not referral.agent.is_active:
        return None
    amount = Decimal(str(payment_amount))
    commission = Commission.objects.create(
        agent=referral.agent,
        company=company,
        plan_name=plan_name,
        payment_amount=amount,
        commission_percentage=referral.agent.commission_percentage,
        commission_amount=calculate_commission_amount(amount, referral.agent.commission_percentage),
        currency=currency,
        payment_reference=payment_reference,
    )
    create_referral_notification(
        recipient=referral.agent.user,
        event_type=ReferralNotification.TYPE_COMMISSION,
        title="Comision generada",
        message=f"Se genero una comision por {company.name}.",
        data={"commission_id": commission.id},
    )
    return commission


@transaction.atomic
def approve_commission(*, commission, approved_by):
    if commission.status != Commission.STATUS_PENDING:
        raise ValueError("Only pending commissions can be approved.")
    commission.status = Commission.STATUS_APPROVED
    commission.approved_at = timezone.now()
    commission.save(update_fields=["status", "approved_at"])
    create_referral_notification(
        recipient=commission.agent.user,
        event_type=ReferralNotification.TYPE_APPROVED,
        title="Comision aprobada",
        message=f"Tu comision de {commission.commission_amount} {commission.currency} fue aprobada.",
        data={"commission_id": commission.id, "approved_by": approved_by.id},
    )
    return commission


@transaction.atomic
def mark_commission_paid(*, commission, paid_by):
    if commission.status not in {Commission.STATUS_APPROVED, Commission.STATUS_PENDING}:
        raise ValueError("Only pending or approved commissions can be marked as paid.")
    commission.status = Commission.STATUS_PAID
    commission.paid_at = timezone.now()
    if not commission.approved_at:
        commission.approved_at = timezone.now()
    commission.save(update_fields=["status", "paid_at", "approved_at"])
    create_referral_notification(
        recipient=commission.agent.user,
        event_type=ReferralNotification.TYPE_PAID,
        title="Comision pagada",
        message=f"Tu comision de {commission.commission_amount} {commission.currency} fue marcada como pagada.",
        data={"commission_id": commission.id, "paid_by": paid_by.id},
    )
    return commission


def agent_stats(agent):
    commissions = agent.commissions.all()
    return {
        "registered_companies": agent.referrals.filter(referred_company__isnull=False).count(),
        "referrals": agent.referrals.count(),
        "card_sales": agent.card_sales.count(),
        "pending_commissions": commissions.filter(status=Commission.STATUS_PENDING).aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00"),
        "paid_commissions": commissions.filter(status=Commission.STATUS_PAID).aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00"),
        "sold_plans": commissions.count(),
    }


def admin_stats():
    commissions = Commission.objects.all()
    return {
        "total_agents": AgentProfile.objects.count(),
        "registered_companies": Referral.objects.filter(referred_company__isnull=False).count(),
        "premium_companies": commissions.values("company").distinct().count(),
        "pending_commissions": commissions.filter(status=Commission.STATUS_PENDING).aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00"),
        "paid_commissions": commissions.filter(status=Commission.STATUS_PAID).aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00"),
        "generated_revenue": commissions.aggregate(total=Sum("payment_amount"))["total"] or Decimal("0.00"),
        "top_agents": AgentProfile.objects.annotate(total_referrals=Count("referrals")).order_by("-total_referrals", "agent_id")[:5],
    }
