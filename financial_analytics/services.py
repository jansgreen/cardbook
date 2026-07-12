from decimal import Decimal
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from billing.models import Invoice, Payment, Refund, StripeEvent
from companies.models import Company
from financial_analytics.models import AuditLog, CommissionPayment, ReferralClick, RevenueSnapshot
from referrals.models import AgentProfile, Commission
from subscriptions.models import Subscription


ZERO = Decimal("0.00")


class FinanceConfigurationError(Exception):
    pass


class FinanceValidationError(Exception):
    pass


def get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise FinanceConfigurationError("Stripe is not configured.")
    try:
        import stripe
    except ImportError as exc:
        raise FinanceConfigurationError("The stripe package is not installed.") from exc
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def decimal_to_minor_units(amount):
    return int((Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1")))


def minor_units_to_decimal(amount):
    return (Decimal(str(amount or 0)) / Decimal("100")).quantize(Decimal("0.01"))


def stripe_timestamp(value):
    if not value:
        return None
    try:
        return timezone.datetime.fromtimestamp(int(value), tz=timezone.get_current_timezone())
    except (TypeError, ValueError, OSError):
        return None


def payment_refunded_amount(payment):
    return money_sum(payment.refunds.exclude(status__in=[Refund.STATUS_FAILED, Refund.STATUS_CANCELLED]), "amount")


def payment_refundable_amount(payment):
    return (Decimal(payment.amount) - payment_refunded_amount(payment)).quantize(Decimal("0.01"))


def get_request_ip(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_audit_log(*, action, title, actor=None, message="", target=None, target_type="", target_id="", metadata=None, severity=AuditLog.SEVERITY_INFO, request=None):
    resolved_target_type = target_type
    resolved_target_id = str(target_id or "")
    if target is not None:
        resolved_target_type = resolved_target_type or f"{target.__class__.__module__}.{target.__class__.__name__}"
        resolved_target_id = resolved_target_id or str(getattr(target, "pk", ""))
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        severity=severity,
        target_type=resolved_target_type,
        target_id=resolved_target_id,
        title=title,
        message=message,
        metadata=metadata or {},
        ip_address=get_request_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:1000] if request else ""),
    )


def money_sum(queryset, field):
    return queryset.aggregate(total=Coalesce(Sum(field), ZERO))["total"] or ZERO


def active_subscriptions():
    return Subscription.objects.filter(status__in=[Subscription.STATUS_ACTIVE, Subscription.STATUS_TRIALING])


def calculate_mrr(subscriptions=None):
    subscriptions = subscriptions or active_subscriptions()
    total = ZERO
    for subscription in subscriptions:
        total += Decimal(subscription.normalized_mrr)
    return total.quantize(Decimal("0.01"))


def calculate_arr(subscriptions=None):
    return (calculate_mrr(subscriptions) * Decimal("12")).quantize(Decimal("0.01"))


def calculate_net_revenue(payments=None, refunds=None, commissions=None):
    payments = payments or Payment.objects.filter(status=Payment.STATUS_SUCCEEDED)
    refunds = refunds or Refund.objects.filter(status=Refund.STATUS_SUCCEEDED)
    commissions = commissions or Commission.objects.exclude(status=Commission.STATUS_CANCELLED)
    gross = money_sum(payments, "amount")
    stripe_fees = money_sum(payments, "stripe_fee")
    refund_total = money_sum(refunds, "amount")
    commission_total = money_sum(commissions, "commission_amount")
    return (gross - stripe_fees - refund_total - commission_total).quantize(Decimal("0.01"))


def calculate_churn_rate(period_start=None, period_end=None):
    period_end = period_end or timezone.now()
    period_start = period_start or period_end.replace(day=1)
    active_at_start = Subscription.objects.filter(created_at__lte=period_start).exclude(status=Subscription.STATUS_CANCELLED).count()
    cancelled = Subscription.objects.filter(status=Subscription.STATUS_CANCELLED, updated_at__range=(period_start, period_end)).count()
    if active_at_start == 0:
        return Decimal("0.00")
    return ((Decimal(cancelled) / Decimal(active_at_start)) * Decimal("100")).quantize(Decimal("0.01"))


def calculate_agent_conversion(agent):
    agent_id = getattr(agent, "id", agent)
    clicks = ReferralClick.objects.filter(agent_id=agent_id).count()
    subscribed_companies = Commission.objects.filter(agent_id=agent_id).values("company_id").distinct().count()
    if clicks == 0:
        return Decimal("0.00")
    return ((Decimal(subscribed_companies) / Decimal(clicks)) * Decimal("100")).quantize(Decimal("0.01"))


def create_commission_from_payment(payment, agent, percentage):
    if not isinstance(agent, AgentProfile):
        agent, _ = AgentProfile.objects.get_or_create(user=agent)
    percentage = Decimal(str(percentage))
    amount = ((payment.amount * percentage) / Decimal("100")).quantize(Decimal("0.01"))
    commission, _ = Commission.objects.get_or_create(
        payment=payment,
        defaults={
            "agent": agent,
            "company": payment.company,
            "subscription": payment.subscription,
            "plan_name": payment.subscription.plan if payment.subscription else "",
            "payment_amount": payment.amount,
            "commission_percentage": percentage,
            "commission_amount": amount,
            "currency": payment.currency,
            "payment_reference": payment.stripe_payment_intent_id,
        },
    )
    if _:
        create_audit_log(
            action=AuditLog.ACTION_COMMISSION_GENERATED,
            title="Comision generada por pago",
            target=commission,
            metadata={
                "payment_id": payment.id,
                "company_id": payment.company_id,
                "agent_id": agent.id,
                "amount": str(amount),
            },
        )
    return commission


def approve_commission(commission, approved_by, request=None):
    if commission.status != Commission.STATUS_PENDING:
        return commission
    commission.status = Commission.STATUS_APPROVED
    commission.approved_by = approved_by
    commission.approved_at = timezone.now()
    commission.save(update_fields=["status", "approved_by", "approved_at"])
    create_audit_log(
        action=AuditLog.ACTION_COMMISSION_APPROVED,
        title="Comision aprobada",
        actor=approved_by,
        target=commission,
        message=f"Comision {commission.id} aprobada para {commission.agent}.",
        metadata={
            "commission_id": commission.id,
            "agent_id": commission.agent_id,
            "company_id": commission.company_id,
            "amount": str(commission.commission_amount),
            "currency": commission.currency,
        },
        request=request,
    )
    return commission


def mark_commission_paid(commission, paid_by, request=None):
    if commission.status not in {Commission.STATUS_PENDING, Commission.STATUS_APPROVED}:
        return commission
    commission.status = Commission.STATUS_PAID
    commission.paid_by = paid_by
    commission.paid_at = timezone.now()
    commission.save(update_fields=["status", "paid_by", "paid_at"])
    create_audit_log(
        action=AuditLog.ACTION_COMMISSION_PAID,
        title="Comision marcada como pagada",
        actor=paid_by,
        target=commission,
        message=f"Comision {commission.id} marcada como pagada para {commission.agent}.",
        metadata={
            "commission_id": commission.id,
            "agent_id": commission.agent_id,
            "company_id": commission.company_id,
            "amount": str(commission.commission_amount),
            "currency": commission.currency,
        },
        request=request,
    )
    return commission


def create_customer_portal_session(*, company, request, return_url=""):
    subscription = company.subscriptions.exclude(stripe_customer_id="").order_by("-updated_at").first()
    if not subscription or not subscription.stripe_customer_id:
        raise FinanceValidationError("This company has no Stripe customer.")
    stripe = get_stripe_client()
    resolved_return_url = return_url or settings.STRIPE_CUSTOMER_PORTAL_RETURN_URL
    if resolved_return_url.startswith("/"):
        resolved_return_url = request.build_absolute_uri(resolved_return_url)
    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=resolved_return_url,
    )
    create_audit_log(
        action=AuditLog.ACTION_CUSTOMER_PORTAL_CREATED,
        title="Portal de cliente Stripe creado",
        actor=request.user,
        target=company,
        metadata={
            "company_id": company.id,
            "stripe_customer_id": subscription.stripe_customer_id,
            "portal_session_id": getattr(session, "id", ""),
        },
        request=request,
    )
    return session


@transaction.atomic
def create_refund_for_payment(*, payment, amount=None, reason="", processed_by=None, request=None, manual=False):
    if payment.status not in {Payment.STATUS_SUCCEEDED, Payment.STATUS_PARTIALLY_REFUNDED}:
        raise FinanceValidationError("Only succeeded or partially refunded payments can be refunded.")
    amount = Decimal(str(amount or payment_refundable_amount(payment))).quantize(Decimal("0.01"))
    if amount <= ZERO:
        raise FinanceValidationError("Refund amount must be greater than zero.")
    refundable_amount = payment_refundable_amount(payment)
    if amount > refundable_amount:
        raise FinanceValidationError("Refund amount exceeds the available refundable balance.")

    stripe_refund_id = ""
    refund_status = Refund.STATUS_PENDING
    mode = "manual"
    if not manual:
        stripe = get_stripe_client()
        stripe_refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id,
            amount=decimal_to_minor_units(amount),
            reason="requested_by_customer",
            metadata={
                "payment_id": str(payment.id),
                "company_id": str(payment.company_id),
                "processed_by": str(getattr(processed_by, "id", "")),
            },
        )
        stripe_refund_id = stripe_refund.id
        refund_status = Refund.STATUS_SUCCEEDED if getattr(stripe_refund, "status", "") == "succeeded" else Refund.STATUS_PENDING
        mode = "stripe"
    elif not settings.STRIPE_ALLOW_MANUAL_REFUNDS:
        raise FinanceConfigurationError("Manual refunds are disabled.")

    if not stripe_refund_id:
        stripe_refund_id = f"manual-{payment.id}-{Refund.objects.count() + 1}"
    refund = Refund.objects.create(
        payment=payment,
        stripe_refund_id=stripe_refund_id,
        amount=amount,
        reason=reason or ("Manual refund" if manual else "Stripe refund"),
        status=refund_status,
        processed_by=processed_by,
    )
    active_refunds = payment_refunded_amount(payment)
    if active_refunds >= payment.amount:
        payment.status = Payment.STATUS_REFUNDED
    elif active_refunds > ZERO:
        payment.status = Payment.STATUS_PARTIALLY_REFUNDED
    payment.save(update_fields=["status"])
    create_audit_log(
        action=AuditLog.ACTION_REFUND_CREATED,
        title="Reembolso creado",
        actor=processed_by,
        target=refund,
        message=f"Reembolso {refund.id} creado para pago {payment.id}.",
        metadata={
            "payment_id": payment.id,
            "company_id": payment.company_id,
            "amount": str(amount),
            "currency": payment.currency,
            "mode": mode,
            "stripe_refund_id": stripe_refund_id,
        },
        request=request,
    )
    return refund


@transaction.atomic
def create_agent_payout(*, agent, paid_by, commission_ids=None, payment_method="", transaction_reference="", notes="", request=None):
    commissions = Commission.objects.select_for_update().filter(agent=agent, status=Commission.STATUS_APPROVED)
    if commission_ids:
        commissions = commissions.filter(id__in=commission_ids)
    commissions = list(commissions)
    if not commissions:
        raise FinanceValidationError("There are no approved commissions to pay for this agent.")
    total_amount = sum((commission.commission_amount for commission in commissions), ZERO).quantize(Decimal("0.01"))
    payout = CommissionPayment.objects.create(
        agent=agent,
        total_amount=total_amount,
        currency=commissions[0].currency,
        payment_method=payment_method,
        transaction_reference=transaction_reference,
        notes=notes,
        paid_by=paid_by,
        paid_at=timezone.now(),
    )
    payout.commissions.set(commissions)
    now = timezone.now()
    for commission in commissions:
        commission.status = Commission.STATUS_PAID
        commission.paid_by = paid_by
        commission.paid_at = now
    Commission.objects.bulk_update(commissions, ["status", "paid_by", "paid_at"])
    create_audit_log(
        action=AuditLog.ACTION_AGENT_PAYOUT_CREATED,
        title="Pago de agente creado",
        actor=paid_by,
        target=payout,
        message=f"Pago por lote creado para {agent}.",
        metadata={
            "agent_id": agent.id,
            "commission_ids": [commission.id for commission in commissions],
            "total_amount": str(total_amount),
            "currency": payout.currency,
            "payment_method": payment_method,
            "transaction_reference": transaction_reference,
        },
        request=request,
    )
    return payout


def average_agent_conversion():
    agent_ids = ReferralClick.objects.values_list("agent_id", flat=True).distinct()
    values = [calculate_agent_conversion(agent_id) for agent_id in agent_ids]
    if not values:
        return Decimal("0.00")
    return (sum(values, ZERO) / Decimal(len(values))).quantize(Decimal("0.01"))


def overview_metrics():
    payments = Payment.objects.filter(status=Payment.STATUS_SUCCEEDED)
    refunds = Refund.objects.filter(status=Refund.STATUS_SUCCEEDED)
    commissions = Commission.objects.exclude(status=Commission.STATUS_CANCELLED)
    return {
        "gross_revenue": money_sum(payments, "amount"),
        "net_revenue": calculate_net_revenue(payments, refunds, commissions),
        "mrr": calculate_mrr(),
        "arr": calculate_arr(),
        "active_subscriptions": active_subscriptions().count(),
        "new_subscriptions": Subscription.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count(),
        "pending_commissions": money_sum(Commission.objects.filter(status=Commission.STATUS_PENDING), "commission_amount"),
        "paid_commissions": money_sum(Commission.objects.filter(status=Commission.STATUS_PAID), "commission_amount"),
        "refunds": money_sum(refunds, "amount"),
        "churn_rate": calculate_churn_rate(),
        "stripe_fees": money_sum(payments, "stripe_fee"),
        "conversion_rate": average_agent_conversion(),
    }


def plan_distribution():
    return list(Subscription.objects.values("plan", "status").annotate(total=Count("id")).order_by("plan"))


def recent_activity(limit=12):
    items = []
    for payment in Payment.objects.select_related("company").order_by("-created_at")[:limit]:
        items.append({
            "type": "payment",
            "title": "Pago recibido" if payment.status == Payment.STATUS_SUCCEEDED else "Pago actualizado",
            "description": payment.company.name,
            "amount": payment.amount,
            "created_at": payment.created_at,
        })
    for commission in Commission.objects.select_related("agent", "company").order_by("-created_at")[:limit]:
        items.append({
            "type": "commission",
            "title": "Comision generada",
            "description": f"{commission.agent} - {commission.company}",
            "amount": commission.commission_amount,
            "created_at": commission.created_at,
        })
    return sorted(items, key=lambda item: item["created_at"], reverse=True)[:limit]


def stripe_object(payload):
    return ((payload.get("data") or {}).get("object") or {}) if isinstance(payload, dict) else {}


def stripe_metadata(obj):
    metadata = obj.get("metadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def resolve_company_from_stripe_object(obj):
    metadata = stripe_metadata(obj)
    company_id = metadata.get("company_id") or metadata.get("cardbook_company_id")
    if company_id:
        company = Company.objects.filter(id=company_id).first()
        if company:
            return company

    subscription_id = obj.get("subscription")
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")
    if subscription_id:
        subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).select_related("company").first()
        if subscription:
            return subscription.company

    invoice_id = obj.get("invoice")
    if isinstance(invoice_id, dict):
        invoice_id = invoice_id.get("id")
    if invoice_id:
        invoice = Invoice.objects.filter(stripe_invoice_id=invoice_id).select_related("company").first()
        if invoice:
            return invoice.company

    customer_id = obj.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    if customer_id:
        subscription = Subscription.objects.filter(stripe_customer_id=customer_id).select_related("company").order_by("-updated_at").first()
        if subscription:
            return subscription.company
    return None


def stripe_subscription_interval(subscription_obj):
    items = ((subscription_obj.get("items") or {}).get("data") or [])
    if not items:
        return Subscription.INTERVAL_MONTHLY
    recurring = (items[0].get("price") or {}).get("recurring") or {}
    return Subscription.INTERVAL_YEARLY if recurring.get("interval") == "year" else Subscription.INTERVAL_MONTHLY


def stripe_subscription_amount(subscription_obj):
    items = ((subscription_obj.get("items") or {}).get("data") or [])
    if not items:
        return ZERO
    return minor_units_to_decimal((items[0].get("price") or {}).get("unit_amount") or 0)


def stripe_subscription_plan(subscription_obj):
    metadata = stripe_metadata(subscription_obj)
    if metadata.get("plan"):
        return metadata["plan"]
    items = ((subscription_obj.get("items") or {}).get("data") or [])
    if items:
        price = items[0].get("price") or {}
        product = price.get("product")
        if isinstance(product, dict):
            return product.get("name") or product.get("id") or "Stripe plan"
        return price.get("nickname") or price.get("id") or "Stripe plan"
    return "Stripe plan"


def sync_subscription_from_stripe(subscription_obj):
    company = resolve_company_from_stripe_object(subscription_obj)
    if not company:
        raise FinanceValidationError("Stripe subscription could not be matched to a company.")
    stripe_subscription_id = subscription_obj.get("id")
    if not stripe_subscription_id:
        raise FinanceValidationError("Stripe subscription payload has no id.")
    stripe_status = subscription_obj.get("status") or Subscription.STATUS_INCOMPLETE
    status = Subscription.STATUS_CANCELLED if stripe_status == "canceled" else stripe_status
    subscription, _ = Subscription.objects.update_or_create(
        stripe_subscription_id=stripe_subscription_id,
        defaults={
            "company": company,
            "stripe_customer_id": subscription_obj.get("customer") or "",
            "plan": stripe_subscription_plan(subscription_obj),
            "unit_amount": stripe_subscription_amount(subscription_obj),
            "currency": (subscription_obj.get("currency") or "usd").upper(),
            "status": status,
            "billing_interval": stripe_subscription_interval(subscription_obj),
            "current_period_start": stripe_timestamp(subscription_obj.get("current_period_start")),
            "current_period_end": stripe_timestamp(subscription_obj.get("current_period_end")),
            "cancel_at_period_end": bool(subscription_obj.get("cancel_at_period_end")),
            "trial_start": stripe_timestamp(subscription_obj.get("trial_start")),
            "trial_end": stripe_timestamp(subscription_obj.get("trial_end")),
        },
    )
    return subscription


def sync_invoice_from_stripe(invoice_obj):
    company = resolve_company_from_stripe_object(invoice_obj)
    if not company:
        raise FinanceValidationError("Stripe invoice could not be matched to a company.")
    stripe_invoice_id = invoice_obj.get("id")
    if not stripe_invoice_id:
        raise FinanceValidationError("Stripe invoice payload has no id.")
    subscription_id = invoice_obj.get("subscription")
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")
    subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first() if subscription_id else None
    invoice, _ = Invoice.objects.update_or_create(
        stripe_invoice_id=stripe_invoice_id,
        defaults={
            "company": company,
            "subscription": subscription,
            "invoice_number": invoice_obj.get("number") or "",
            "subtotal": minor_units_to_decimal(invoice_obj.get("subtotal") or 0),
            "tax": minor_units_to_decimal(invoice_obj.get("tax") or 0),
            "total": minor_units_to_decimal(invoice_obj.get("total") or 0),
            "amount_paid": minor_units_to_decimal(invoice_obj.get("amount_paid") or 0),
            "amount_due": minor_units_to_decimal(invoice_obj.get("amount_due") or 0),
            "currency": (invoice_obj.get("currency") or "usd").upper(),
            "status": invoice_obj.get("status") or Invoice.STATUS_DRAFT,
            "hosted_invoice_url": invoice_obj.get("hosted_invoice_url") or "",
            "invoice_pdf": invoice_obj.get("invoice_pdf") or "",
            "due_date": stripe_timestamp(invoice_obj.get("due_date")),
            "paid_at": stripe_timestamp((invoice_obj.get("status_transitions") or {}).get("paid_at")),
        },
    )
    return invoice


def sync_payment_intent_from_stripe(payment_obj):
    company = resolve_company_from_stripe_object(payment_obj)
    if not company:
        raise FinanceValidationError("Stripe payment intent could not be matched to a company.")
    payment_intent_id = payment_obj.get("id")
    if not payment_intent_id:
        raise FinanceValidationError("Stripe payment intent payload has no id.")
    invoice_id = payment_obj.get("invoice")
    if isinstance(invoice_id, dict):
        invoice_id = invoice_id.get("id")
    invoice = Invoice.objects.filter(stripe_invoice_id=invoice_id).select_related("subscription").first() if invoice_id else None
    subscription = invoice.subscription if invoice else company.subscriptions.order_by("-updated_at").first()
    stripe_status = payment_obj.get("status")
    status = Payment.STATUS_PENDING
    if stripe_status == "succeeded":
        status = Payment.STATUS_SUCCEEDED
    elif stripe_status in {"canceled", "requires_payment_method"}:
        status = Payment.STATUS_FAILED
    amount = minor_units_to_decimal(payment_obj.get("amount_received") or payment_obj.get("amount") or 0)
    payment, _ = Payment.objects.update_or_create(
        stripe_payment_intent_id=payment_intent_id,
        defaults={
            "company": company,
            "subscription": subscription,
            "invoice": invoice,
            "stripe_invoice_id": invoice_id or "",
            "amount": amount,
            "currency": (payment_obj.get("currency") or "usd").upper(),
            "status": status,
            "payment_method": payment_obj.get("payment_method_types", [""])[0] if payment_obj.get("payment_method_types") else "",
            "net_amount": amount,
            "paid_at": stripe_timestamp(payment_obj.get("created")) if status == Payment.STATUS_SUCCEEDED else None,
        },
    )
    return payment


def sync_refund_from_stripe(refund_obj):
    refund_id = refund_obj.get("id")
    if not refund_id:
        raise FinanceValidationError("Stripe refund payload has no id.")
    payment_intent_id = refund_obj.get("payment_intent")
    if isinstance(payment_intent_id, dict):
        payment_intent_id = payment_intent_id.get("id")
    payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
    if not payment:
        raise FinanceValidationError("Stripe refund could not be matched to a payment.")
    status_map = {
        "succeeded": Refund.STATUS_SUCCEEDED,
        "failed": Refund.STATUS_FAILED,
        "canceled": Refund.STATUS_CANCELLED,
        "pending": Refund.STATUS_PENDING,
    }
    refund, _ = Refund.objects.update_or_create(
        stripe_refund_id=refund_id,
        defaults={
            "payment": payment,
            "amount": minor_units_to_decimal(refund_obj.get("amount") or 0),
            "reason": refund_obj.get("reason") or "Stripe refund",
            "status": status_map.get(refund_obj.get("status"), Refund.STATUS_PENDING),
        },
    )
    active_refunds = payment_refunded_amount(payment)
    if active_refunds >= payment.amount:
        payment.status = Payment.STATUS_REFUNDED
    elif active_refunds > ZERO:
        payment.status = Payment.STATUS_PARTIALLY_REFUNDED
    payment.save(update_fields=["status"])
    return refund


def sync_stripe_event_payload(event_type, payload):
    obj = stripe_object(payload)
    if event_type.startswith("customer.subscription."):
        return sync_subscription_from_stripe(obj)
    if event_type.startswith("invoice."):
        return sync_invoice_from_stripe(obj)
    if event_type.startswith("payment_intent."):
        return sync_payment_intent_from_stripe(obj)
    if event_type.startswith("refund."):
        return sync_refund_from_stripe(obj)
    return None


@transaction.atomic
def process_stripe_webhook(event_id, event_type, payload):
    event, created = StripeEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type, "payload": payload},
    )
    if not created:
        return {"processed": False, "event_id": event.event_id, "event_type": event.event_type, "synced": False}

    synced_target = None
    warning = ""
    try:
        synced_target = sync_stripe_event_payload(event_type, payload)
    except FinanceValidationError as exc:
        warning = str(exc)

    metadata = {"event_id": event_id, "event_type": event_type, "synced": bool(synced_target)}
    if synced_target:
        metadata["synced_target_type"] = f"{synced_target.__class__.__module__}.{synced_target.__class__.__name__}"
        metadata["synced_target_id"] = getattr(synced_target, "id", "")
    if warning:
        metadata["warning"] = warning

    create_audit_log(
        action=AuditLog.ACTION_STRIPE_WEBHOOK,
        title="Webhook Stripe procesado" if not warning else "Webhook Stripe recibido con advertencia",
        target=event,
        target_type="billing.StripeEvent",
        target_id=event.event_id,
        message=warning,
        severity=AuditLog.SEVERITY_WARNING if warning else AuditLog.SEVERITY_INFO,
        metadata=metadata,
    )
    return {
        "processed": True,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "synced": bool(synced_target),
        "warning": warning,
    }


def verify_stripe_signature(raw_payload, signature_header, webhook_secret, tolerance_seconds=300):
    if not webhook_secret:
        return False
    if not signature_header:
        return False
    parts = {}
    for item in signature_header.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts.setdefault(key, []).append(value)
    timestamp_values = parts.get("t") or []
    signature_values = parts.get("v1") or []
    if not timestamp_values or not signature_values:
        return False
    timestamp = timestamp_values[0]
    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - timestamp_int) > tolerance_seconds:
        return False
    signed_payload = timestamp.encode("utf-8") + b"." + raw_payload
    expected = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, value) for value in signature_values)


def parse_stripe_payload(raw_payload):
    try:
        return json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def generate_revenue_snapshot(period_type=RevenueSnapshot.PERIOD_MONTHLY, period_start=None, period_end=None):
    now = timezone.now().date()
    period_start = period_start or now.replace(day=1)
    period_end = period_end or now
    payments = Payment.objects.filter(status=Payment.STATUS_SUCCEEDED, created_at__date__range=(period_start, period_end))
    refunds = Refund.objects.filter(status=Refund.STATUS_SUCCEEDED, created_at__date__range=(period_start, period_end))
    commissions = Commission.objects.filter(created_at__date__range=(period_start, period_end)).exclude(status=Commission.STATUS_CANCELLED)
    snapshot, _ = RevenueSnapshot.objects.update_or_create(
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        defaults={
            "gross_revenue": money_sum(payments, "amount"),
            "net_revenue": calculate_net_revenue(payments, refunds, commissions),
            "stripe_fees": money_sum(payments, "stripe_fee"),
            "refunds": money_sum(refunds, "amount"),
            "commissions_generated": money_sum(commissions, "commission_amount"),
            "commissions_paid": money_sum(commissions.filter(status=Commission.STATUS_PAID), "commission_amount"),
            "active_subscriptions": active_subscriptions().count(),
            "new_subscriptions": Subscription.objects.filter(created_at__date__range=(period_start, period_end)).count(),
            "cancelled_subscriptions": Subscription.objects.filter(status=Subscription.STATUS_CANCELLED, updated_at__date__range=(period_start, period_end)).count(),
        },
    )
    return snapshot


def generate_financial_report(report_key):
    reports = {
        "monthly": "Reporte mensual",
        "annual": "Reporte anual",
        "by_plan": "Reporte por plan",
        "by_agent": "Reporte por agente",
        "commissions": "Reporte de comisiones",
        "refunds": "Reporte de reembolsos",
        "companies": "Reporte de empresas",
        "churn": "Reporte de churn",
    }
    return {
        "key": report_key,
        "name": reports.get(report_key, "Reporte financiero"),
        "generated_at": timezone.now(),
        "formats": ["csv", "xlsx", "pdf"],
        "metrics": overview_metrics(),
    }
