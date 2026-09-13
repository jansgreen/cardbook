import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView

from billing.models import Invoice, Payment, Refund
from cardbookweb.responses import StandardPagination, error_response, success_response
from companies.models import Company
from financial_analytics.models import CommissionPayment, ReferralClick
from financial_analytics.models import AuditLog
from referrals.models import AgentProfile, Commission
from subscriptions.models import Subscription
from .permissions import can_view_company_billing, has_finance_permission
from .serializers import (
    CommissionPaymentSerializer,
    CommissionSerializer,
    FinanceCompanySerializer,
    InvoiceSerializer,
    PaymentSerializer,
    ReferralClickSerializer,
    RefundSerializer,
    SubscriptionSerializer,
)
from .services import (
    approve_commission,
    active_subscriptions,
    generate_financial_report,
    mark_commission_paid,
    overview_metrics,
    parse_stripe_payload,
    plan_distribution,
    process_stripe_webhook,
    recent_activity,
    verify_stripe_signature,
    create_audit_log,
    create_agent_payout,
    create_customer_portal_session,
    create_refund_for_payment,
    get_stripe_webhook_secret,
    payment_refundable_amount,
    FinanceConfigurationError,
    FinanceValidationError,
)


class FinancePermissionMixin:
    permission_key = "dashboard"

    def check_finance_permission(self, request):
        if has_finance_permission(request.user, self.permission_key):
            return None
        return error_response("You do not have permission to access this financial resource.", status_code=status.HTTP_403_FORBIDDEN)


class FinanceWebViewMixin:
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


def paginate(request, queryset, serializer_class):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def filtered_commissions_for_request(request):
    queryset = Commission.objects.select_related("agent", "agent__user", "company", "subscription", "payment").order_by("-created_at")
    status_filter = request.GET.get("status", "").strip()
    agent_id = request.GET.get("agent", "").strip()
    company_id = request.GET.get("company", "").strip()
    date_from = parse_date(request.GET.get("date_from", "").strip() or "")
    date_to = parse_date(request.GET.get("date_to", "").strip() or "")
    search = request.GET.get("q", "").strip()

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if agent_id.isdigit():
        queryset = queryset.filter(agent_id=agent_id)
    if company_id.isdigit():
        queryset = queryset.filter(company_id=company_id)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    if search:
        queryset = queryset.filter(
            Q(agent__user__username__icontains=search)
            | Q(agent__user__email__icontains=search)
            | Q(agent__user__first_name__icontains=search)
            | Q(agent__user__last_name__icontains=search)
            | Q(company__name__icontains=search)
            | Q(plan_name__icontains=search)
            | Q(payment_reference__icontains=search)
        )
    return queryset


def write_csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


class FinanceDashboardView(FinanceWebViewMixin, APIView):

    def get(self, request):
        if not has_finance_permission(request.user, "dashboard"):
            return render(request, "dashboard/finance/forbidden.html", status=403)
        context = {
            "section": "overview",
            "metrics": overview_metrics(),
            "plan_distribution": plan_distribution(),
            "activity": recent_activity(),
            "stripe_dashboard_url": settings.STRIPE_DASHBOARD_URL,
            "can_open_stripe": has_finance_permission(request.user, "stripe"),
        }
        return render(request, "dashboard/finance/overview.html", context)


class FinanceSectionPageView(FinanceWebViewMixin, APIView):
    section = "overview"
    permission_key = "dashboard"
    template_name = "dashboard/finance/section.html"

    def get(self, request):
        if not has_finance_permission(request.user, self.permission_key):
            return render(request, "dashboard/finance/forbidden.html", status=403)
        context = self.get_context_data(request)
        context.update({
            "section": self.section,
            "metrics": overview_metrics(),
            "can_open_stripe": has_finance_permission(request.user, "stripe"),
            "stripe_dashboard_url": settings.STRIPE_DASHBOARD_URL,
        })
        return render(request, self.template_name, context)

    def post(self, request):
        if self.section == "payments":
            return self.post_payment_action(request)
        if self.section != "commissions":
            return redirect(reverse("finance-dashboard"))
        action = request.POST.get("action")
        commission = get_object_or_404(Commission, pk=request.POST.get("commission_id"))
        if action == "approve_commission":
            if not has_finance_permission(request.user, "approve_commissions"):
                messages.error(request, "No tienes permiso para aprobar comisiones.")
                return redirect(reverse("finance-commissions"))
            approve_commission(commission, request.user, request=request)
            messages.success(request, "Comision aprobada.")
        elif action == "mark_commission_paid":
            if not has_finance_permission(request.user, "mark_commissions_paid"):
                messages.error(request, "No tienes permiso para marcar comisiones como pagadas.")
                return redirect(reverse("finance-commissions"))
            mark_commission_paid(commission, request.user, request=request)
            messages.success(request, "Comision marcada como pagada.")
        return redirect(reverse("finance-commissions"))

    def post_payment_action(self, request):
        if request.POST.get("action") != "refund_payment":
            return redirect(reverse("finance-payments"))
        if not has_finance_permission(request.user, "refunds"):
            messages.error(request, "No tienes permiso para procesar reembolsos.")
            return redirect(reverse("finance-payments"))
        payment = get_object_or_404(Payment, pk=request.POST.get("payment_id"))
        manual = str(request.POST.get("manual", "")).lower() in {"1", "true", "yes", "on"}
        try:
            refund = create_refund_for_payment(
                payment=payment,
                amount=request.POST.get("amount"),
                reason=request.POST.get("reason", ""),
                processed_by=request.user,
                request=request,
                manual=manual,
            )
        except FinanceValidationError as exc:
            messages.error(request, str(exc))
        except FinanceConfigurationError as exc:
            create_audit_log(
                action=AuditLog.ACTION_REFUND_FAILED,
                title="Reembolso no procesado",
                actor=request.user,
                target=payment,
                message=str(exc),
                severity=AuditLog.SEVERITY_WARNING,
                request=request,
            )
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Reembolso {refund.stripe_refund_id} creado correctamente.")
        return redirect(reverse("finance-payments"))

    def get_context_data(self, request):
        mapping = {
            "revenue": self.revenue_context,
            "subscriptions": self.subscriptions_context,
            "companies": self.companies_context,
            "referrals": self.referrals_context,
            "commissions": self.commissions_context,
            "payments": self.payments_context,
            "refunds": self.refunds_context,
            "reports": self.reports_context,
            "audit": self.audit_context,
        }
        return mapping.get(self.section, self.revenue_context)()

    def revenue_context(self):
        payments = Payment.objects.select_related("company", "subscription", "invoice").order_by("-created_at")
        return {
            "title": "Ingresos",
            "subtitle": "Pagos, neto, fees de Stripe y comisiones asociadas.",
            "table_columns": ["Fecha", "Empresa", "Plan", "Factura", "Monto bruto", "Stripe Fee", "Neto", "Estado"],
            "table_rows": [
                [p.created_at, p.company.name, p.subscription.plan if p.subscription else "-", p.stripe_invoice_id or "-", p.amount, p.stripe_fee, p.net_amount, p.status]
                for p in payments[:100]
            ],
            "summary_cards": [
                ("Ingresos hoy", "$0.00", "Periodo actual"),
                ("Ingresos del mes", f"${overview_metrics()['gross_revenue']}", "Pagos exitosos"),
                ("Ingresos netos", f"${overview_metrics()['net_revenue']}", "Luego de costos"),
                ("Stripe Fees", f"${overview_metrics()['stripe_fees']}", "Costo de procesamiento"),
            ],
        }

    def subscriptions_context(self):
        subscriptions = Subscription.objects.select_related("company").order_by("-updated_at")
        return {
            "title": "Suscripciones",
            "subtitle": "Planes activos, trials, renovaciones y estados de cobro.",
            "table_columns": ["Empresa", "Plan", "Estado", "Precio", "Periodicidad", "Inicio", "Proxima renovacion", "Stripe Customer"],
            "table_rows": [
                [s.company.name, s.plan, s.status, s.unit_amount, s.billing_interval, s.current_period_start or "-", s.current_period_end or "-", s.stripe_customer_id or "-"]
                for s in subscriptions[:100]
            ],
            "summary_cards": [
                ("Activas", Subscription.objects.filter(status=Subscription.STATUS_ACTIVE).count(), "Cobro normal"),
                ("En trial", Subscription.objects.filter(status=Subscription.STATUS_TRIALING).count(), "Prueba"),
                ("Past due", Subscription.objects.filter(status=Subscription.STATUS_PAST_DUE).count(), "Atencion requerida"),
                ("Canceladas", Subscription.objects.filter(status=Subscription.STATUS_CANCELLED).count(), "Historico"),
            ],
        }

    def companies_context(self):
        companies = Company.objects.select_related("owner").prefetch_related("subscriptions").order_by("name")
        rows = []
        for company in companies[:100]:
            subscription = company.subscriptions.order_by("-updated_at").first()
            rows.append([
                company.name,
                company.owner.email,
                company.email or "-",
                subscription.plan if subscription else "-",
                subscription.status if subscription else "sin_plan",
                subscription.normalized_mrr if subscription else 0,
                company.created_at,
            ])
        return {
            "title": "Empresas suscritas",
            "subtitle": "Vista administrativa de empresas, owners, plan y MRR.",
            "table_columns": ["Empresa", "Owner", "Email", "Plan", "Estado", "MRR", "Registro"],
            "table_rows": rows,
            "summary_cards": [
                ("Empresas", companies.count(), "Total"),
                ("Con plan activo", active_subscriptions().count(), "Activas o trial"),
                ("Sin plan", Company.objects.filter(subscriptions__isnull=True).count(), "Oportunidad"),
                ("MRR", f"${overview_metrics()['mrr']}", "Normalizado"),
            ],
        }

    def referrals_context(self):
        agents = AgentProfile.objects.filter(finance_referral_clicks__isnull=False).select_related("user").distinct()
        rows = []
        for index, agent in enumerate(agents, start=1):
            rows.append([
                index,
                agent.user.get_full_name() or agent.user.username,
                ReferralClick.objects.filter(agent=agent).first().referral_code if ReferralClick.objects.filter(agent=agent).exists() else "-",
                ReferralClick.objects.filter(agent=agent).count(),
                Commission.objects.filter(agent=agent).values("company_id").distinct().count(),
                sum((c.payment_amount for c in Commission.objects.filter(agent=agent)), 0),
                sum((c.commission_amount for c in Commission.objects.filter(agent=agent)), 0),
            ])
        return {
            "title": "Agentes y referidos",
            "subtitle": "Ranking de agentes, conversion y comisiones generadas.",
            "table_columns": ["#", "Agente", "Codigo", "Clicks", "Empresas", "Ventas", "Comision"],
            "table_rows": rows,
            "summary_cards": [
                ("Agentes activos", agents.count(), "Con clicks"),
                ("Clicks", ReferralClick.objects.count(), "Referidos"),
                ("Ventas generadas", f"${sum((c.payment_amount for c in Commission.objects.all()), 0)}", "Base"),
                ("Comisiones", f"${sum((c.commission_amount for c in Commission.objects.all()), 0)}", "Generadas"),
            ],
        }

    def commissions_context(self):
        commissions = filtered_commissions_for_request(self.request)
        generated_total = sum((c.commission_amount for c in commissions), 0)
        return {
            "title": "Comisiones",
            "subtitle": "Historial completo de comisiones, aprobaciones y pagos.",
            "commissions": commissions[:100],
            "commission_filters": self.request.GET,
            "commission_statuses": Commission.STATUS_CHOICES,
            "commission_agents": AgentProfile.objects.select_related("user").order_by("user__first_name", "user__username"),
            "commission_companies": Company.objects.order_by("name"),
            "commission_export_url": f"{reverse('finance-report-csv', args=['commissions'])}?{self.request.GET.urlencode()}",
            "can_approve_commissions": has_finance_permission(self.request.user, "approve_commissions") if hasattr(self, "request") else False,
            "can_mark_commissions_paid": has_finance_permission(self.request.user, "mark_commissions_paid") if hasattr(self, "request") else False,
            "table_columns": ["Fecha", "Agente", "Empresa", "Plan", "Pago base", "%", "Comision", "Estado"],
            "table_rows": [
                [c.created_at, c.agent.user.get_full_name() or c.agent.user.username, c.company.name, c.plan_name, c.payment_amount, c.commission_percentage, c.commission_amount, c.status]
                for c in commissions[:100]
            ],
            "summary_cards": [
                ("Total generado", f"${generated_total}", "Segun filtros"),
                ("Pendiente", commissions.filter(status=Commission.STATUS_PENDING).count(), "Por revisar"),
                ("Aprobado", commissions.filter(status=Commission.STATUS_APPROVED).count(), "Listo para pago"),
                ("Pagado", commissions.filter(status=Commission.STATUS_PAID).count(), "Cerrado"),
            ],
        }

    def payments_context(self):
        payments = list(Payment.objects.select_related("company", "invoice").order_by("-created_at")[:100])
        for payment in payments:
            payment.refundable_amount = payment_refundable_amount(payment)
        return {
            "title": "Pagos",
            "subtitle": "Pagos recibidos, PaymentIntent, invoice, fees y neto.",
            "payments": payments,
            "can_process_refunds": has_finance_permission(self.request.user, "refunds") if hasattr(self, "request") else False,
            "manual_refunds_enabled": settings.STRIPE_ALLOW_MANUAL_REFUNDS,
            "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
            "table_columns": ["Fecha", "Empresa", "Invoice", "Payment Intent", "Monto", "Moneda", "Metodo", "Neto", "Estado"],
            "table_rows": [
                [p.created_at, p.company.name, p.stripe_invoice_id or "-", p.stripe_payment_intent_id, p.amount, p.currency, p.payment_method or "-", p.net_amount, p.status]
                for p in payments
            ],
            "summary_cards": [
                ("Pagos", Payment.objects.count(), "Total"),
                ("Exitosos", Payment.objects.filter(status=Payment.STATUS_SUCCEEDED).count(), "Succeeded"),
                ("Fallidos", Payment.objects.filter(status=Payment.STATUS_FAILED).count(), "Failed"),
                ("Neto", f"${overview_metrics()['net_revenue']}", "Disponible"),
            ],
        }

    def refunds_context(self):
        refunds = Refund.objects.select_related("payment", "payment__company").order_by("-created_at")
        return {
            "title": "Reembolsos",
            "subtitle": "Refunds pendientes, completados y trazabilidad de procesamiento.",
            "table_columns": ["Fecha", "Empresa", "Pago", "Monto original", "Reembolso", "Motivo", "Estado"],
            "table_rows": [
                [r.created_at, r.payment.company.name, r.payment.stripe_payment_intent_id, r.payment.amount, r.amount, r.reason or "-", r.status]
                for r in refunds[:100]
            ],
            "summary_cards": [
                ("Total reembolsado", f"${sum((r.amount for r in refunds), 0)}", "Historico"),
                ("Pendientes", Refund.objects.filter(status=Refund.STATUS_PENDING).count(), "Por procesar"),
                ("Completados", Refund.objects.filter(status=Refund.STATUS_SUCCEEDED).count(), "Succeeded"),
                ("Fallidos", Refund.objects.filter(status=Refund.STATUS_FAILED).count(), "Failed"),
            ],
        }

    def reports_context(self):
        reports = [generate_financial_report(key) for key in ["monthly", "annual", "by_plan", "by_agent", "commissions", "refunds", "companies", "churn"]]
        return {
            "title": "Reportes",
            "subtitle": "Reportes descargables para operacion financiera.",
            "reports": reports,
            "report_exports": [
                {"key": "commissions", "name": "Comisiones", "description": "Detalle filtrable de comisiones por agente, empresa, estado y fecha."},
                {"key": "agents", "name": "Agentes", "description": "Resumen de agentes, referidos, tarjetas creadas y comisiones."},
                {"key": "payments", "name": "Pagos", "description": "Pagos recibidos, neto, fees y estado."},
                {"key": "refunds", "name": "Reembolsos", "description": "Reembolsos por pago, empresa, estado y motivo."},
                {"key": "subscriptions", "name": "Suscripciones", "description": "Planes, MRR, estado y clientes Stripe."},
                {"key": "companies", "name": "Empresas", "description": "Empresas, owners, plan activo y MRR."},
            ],
            "summary_cards": [
                ("Reportes", len(reports), "Disponibles"),
                ("Formatos", "CSV/XLSX/PDF", "Exportacion"),
                ("Ultima generacion", "-", "Bajo demanda"),
                ("Estado", "Listo", "Operativo"),
            ],
        }

    def audit_context(self):
        logs = AuditLog.objects.select_related("actor").order_by("-created_at")
        action = self.request.GET.get("action", "").strip()
        actor = self.request.GET.get("actor", "").strip()
        if action:
            logs = logs.filter(action=action)
        if actor:
            logs = logs.filter(actor_id=actor)
        return {
            "title": "Auditoria",
            "subtitle": "Bitacora de comisiones, agentes, reportes y eventos administrativos.",
            "audit_logs": logs[:150],
            "audit_actions": AuditLog.objects.order_by("action").values_list("action", flat=True).distinct(),
            "audit_actors": get_user_model().objects.filter(audit_logs__isnull=False).distinct().order_by("username"),
            "audit_filters": self.request.GET,
            "summary_cards": [
                ("Eventos", logs.count(), "Segun filtros"),
                ("Comisiones aprobadas", logs.filter(action=AuditLog.ACTION_COMMISSION_APPROVED).count(), "Auditoria"),
                ("Comisiones pagadas", logs.filter(action=AuditLog.ACTION_COMMISSION_PAID).count(), "Auditoria"),
                ("Reportes exportados", logs.filter(action=AuditLog.ACTION_REPORT_EXPORTED).count(), "Auditoria"),
            ],
        }


class FinanceOverviewAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "dashboard"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return success_response("Financial overview retrieved successfully.", {
            "metrics": overview_metrics(),
            "plan_distribution": plan_distribution(),
            "recent_activity": recent_activity(),
        })


class FinanceRevenueAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "revenue"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Payment.objects.select_related("company", "subscription", "invoice"), PaymentSerializer)


class FinanceSubscriptionsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "subscriptions"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Subscription.objects.select_related("company"), SubscriptionSerializer)


class FinanceCompaniesAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "companies"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Company.objects.select_related("owner").prefetch_related("subscriptions"), FinanceCompanySerializer)


class FinanceAgentsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "referrals"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        data = []
        for agent in AgentProfile.objects.filter(finance_referral_clicks__isnull=False).select_related("user").distinct():
            data.append({
                "id": agent.id,
                "username": agent.user.username,
                "name": agent.user.get_full_name() or agent.user.username,
                "clicks": ReferralClick.objects.filter(agent=agent).count(),
                "commissions": Commission.objects.filter(agent=agent).count(),
            })
        return success_response("Agents retrieved successfully.", data)


class FinanceAgentDetailAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "referrals"

    def get(self, request, agent_id):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        try:
            agent = AgentProfile.objects.select_related("user").get(id=agent_id)
        except AgentProfile.DoesNotExist:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Agent detail retrieved successfully.", {
            "agent": {"id": agent.id, "username": agent.user.username, "name": agent.user.get_full_name() or agent.user.username},
            "referrals": ReferralClickSerializer(ReferralClick.objects.filter(agent=agent)[:50], many=True).data,
            "commissions": CommissionSerializer(Commission.objects.filter(agent=agent)[:50], many=True).data,
        })


class FinanceCommissionsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "commissions"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Commission.objects.select_related("agent", "agent__user", "company", "subscription", "payment"), CommissionSerializer)


class ApproveCommissionAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "approve_commissions"

    def post(self, request, commission_id):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        try:
            commission = Commission.objects.get(id=commission_id)
        except Commission.DoesNotExist:
            return error_response("Commission not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Commission approved.", CommissionSerializer(approve_commission(commission, request.user, request=request)).data)


class MarkCommissionPaidAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "mark_commissions_paid"

    def post(self, request, commission_id):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        try:
            commission = Commission.objects.get(id=commission_id)
        except Commission.DoesNotExist:
            return error_response("Commission not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Commission marked as paid.", CommissionSerializer(mark_commission_paid(commission, request.user, request=request)).data)


class FinancePaymentsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "payments"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Payment.objects.select_related("company", "subscription", "invoice"), PaymentSerializer)


class FinanceRefundsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "refunds"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        return paginate(request, Refund.objects.select_related("payment", "payment__company"), RefundSerializer)


class RefundPaymentAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "refunds"

    def post(self, request, payment_id):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return error_response("Payment not found.", status_code=status.HTTP_404_NOT_FOUND)
        manual = str(request.data.get("manual", "")).lower() in {"1", "true", "yes", "on"}
        try:
            refund = create_refund_for_payment(
                payment=payment,
                amount=request.data.get("amount"),
                reason=request.data.get("reason", ""),
                processed_by=request.user,
                request=request,
                manual=manual,
            )
        except FinanceValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except FinanceConfigurationError as exc:
            create_audit_log(
                action=AuditLog.ACTION_REFUND_FAILED,
                title="Reembolso no procesado",
                actor=request.user,
                target=payment,
                message=str(exc),
                severity=AuditLog.SEVERITY_WARNING,
                request=request,
            )
            return error_response(str(exc), status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        return success_response("Refund created successfully.", RefundSerializer(refund).data, status.HTTP_201_CREATED)


class AgentPayoutCreateAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "mark_commissions_paid"

    def post(self, request, agent_id):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        try:
            agent = AgentProfile.objects.get(id=agent_id)
        except AgentProfile.DoesNotExist:
            return error_response("Agent not found.", status_code=status.HTTP_404_NOT_FOUND)
        commission_ids = request.data.get("commission_ids") or []
        if isinstance(commission_ids, str):
            commission_ids = [value for value in commission_ids.split(",") if value.strip()]
        try:
            payout = create_agent_payout(
                agent=agent,
                paid_by=request.user,
                commission_ids=commission_ids,
                payment_method=request.data.get("payment_method", ""),
                transaction_reference=request.data.get("transaction_reference", ""),
                notes=request.data.get("notes", ""),
                request=request,
            )
        except FinanceValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Agent payout created successfully.", CommissionPaymentSerializer(payout).data, status.HTTP_201_CREATED)


class FinanceReportsAPIView(FinancePermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    permission_key = "reports"

    def get(self, request):
        denied = self.check_finance_permission(request)
        if denied:
            return denied
        reports = [
            {"key": "monthly", "name": "Reporte mensual", "formats": ["csv", "xlsx", "pdf"]},
            {"key": "annual", "name": "Reporte anual", "formats": ["csv", "xlsx", "pdf"]},
            {"key": "by_plan", "name": "Reporte por plan", "formats": ["csv", "xlsx"]},
            {"key": "by_agent", "name": "Reporte por agente", "formats": ["csv", "xlsx"]},
            {"key": "commissions", "name": "Reporte de comisiones", "formats": ["csv", "xlsx", "pdf"]},
            {"key": "refunds", "name": "Reporte de reembolsos", "formats": ["csv", "xlsx"]},
            {"key": "companies", "name": "Reporte de empresas", "formats": ["csv", "xlsx", "pdf"]},
            {"key": "churn", "name": "Reporte de churn", "formats": ["csv", "xlsx", "pdf"]},
        ]
        return success_response("Reports retrieved successfully.", reports)


class FinanceReportCSVView(FinanceWebViewMixin, APIView):

    def get(self, request, report_key):
        if not has_finance_permission(request.user, "reports"):
            return render(request, "dashboard/finance/forbidden.html", status=403)
        create_audit_log(
            action=AuditLog.ACTION_REPORT_EXPORTED,
            title="Reporte CSV exportado",
            actor=request.user,
            target_type="financial_analytics.report",
            target_id=report_key,
            message=f"Se exporto el reporte {report_key}.",
            metadata={"report_key": report_key, "filters": dict(request.GET.items())},
            request=request,
        )
        if report_key == "commissions":
            return self.commissions_csv(request)
        if report_key == "agents":
            return self.agents_csv()
        if report_key == "payments":
            return self.payments_csv()
        if report_key == "refunds":
            return self.refunds_csv()
        if report_key == "subscriptions":
            return self.subscriptions_csv()
        if report_key == "companies":
            return self.companies_csv()
        return write_csv_response(
            "cardbook-report.csv",
            ["Reporte", "Estado"],
            [[report_key, "No disponible"]],
        )

    def commissions_csv(self, request):
        commissions = filtered_commissions_for_request(request)
        return write_csv_response(
            "cardbook-commissions.csv",
            [
                "ID",
                "Fecha",
                "Agente",
                "Agent ID",
                "Empresa",
                "Concepto",
                "Monto base",
                "Porcentaje",
                "Comision",
                "Moneda",
                "Estado",
                "Referencia",
            ],
            [
                [
                    commission.id,
                    commission.created_at.isoformat(),
                    commission.agent.user.get_full_name() or commission.agent.user.username,
                    commission.agent.agent_id,
                    commission.company.name,
                    commission.plan_name,
                    commission.payment_amount,
                    commission.commission_percentage,
                    commission.commission_amount,
                    commission.currency,
                    commission.status,
                    commission.payment_reference,
                ]
                for commission in commissions
            ],
        )

    def agents_csv(self):
        agents = AgentProfile.objects.select_related("user").prefetch_related("card_sales", "commissions", "referrals").order_by("agent_id")
        rows = []
        for agent in agents:
            commissions = agent.commissions.exclude(status=Commission.STATUS_CANCELLED)
            rows.append([
                agent.agent_id,
                agent.user.get_full_name() or agent.user.username,
                agent.user.email,
                agent.referral_code,
                agent.commission_percentage,
                agent.is_active,
                agent.referrals.count(),
                agent.card_sales.count(),
                sum((commission.commission_amount for commission in commissions.filter(status=Commission.STATUS_PENDING)), 0),
                sum((commission.commission_amount for commission in commissions.filter(status=Commission.STATUS_APPROVED)), 0),
                sum((commission.commission_amount for commission in commissions.filter(status=Commission.STATUS_PAID)), 0),
            ])
        return write_csv_response(
            "cardbook-agents.csv",
            ["Agent ID", "Agente", "Email", "Codigo", "% Comision", "Activo", "Referidos", "Tarjetas", "Pendiente", "Aprobado", "Pagado"],
            rows,
        )

    def payments_csv(self):
        payments = Payment.objects.select_related("company", "subscription", "invoice").order_by("-created_at")
        return write_csv_response(
            "cardbook-payments.csv",
            ["ID", "Fecha", "Empresa", "Plan", "Payment Intent", "Invoice", "Monto", "Stripe fee", "Neto", "Moneda", "Estado"],
            [
                [
                    payment.id,
                    payment.created_at.isoformat(),
                    payment.company.name,
                    payment.subscription.plan if payment.subscription else "",
                    payment.stripe_payment_intent_id,
                    payment.stripe_invoice_id,
                    payment.amount,
                    payment.stripe_fee,
                    payment.net_amount,
                    payment.currency,
                    payment.status,
                ]
                for payment in payments
            ],
        )

    def refunds_csv(self):
        refunds = Refund.objects.select_related("payment", "payment__company", "processed_by").order_by("-created_at")
        return write_csv_response(
            "cardbook-refunds.csv",
            ["ID", "Fecha", "Empresa", "Pago", "Refund ID", "Monto", "Motivo", "Estado", "Procesado por"],
            [
                [
                    refund.id,
                    refund.created_at.isoformat(),
                    refund.payment.company.name,
                    refund.payment.stripe_payment_intent_id,
                    refund.stripe_refund_id,
                    refund.amount,
                    refund.reason,
                    refund.status,
                    refund.processed_by.email if refund.processed_by else "",
                ]
                for refund in refunds
            ],
        )

    def subscriptions_csv(self):
        subscriptions = Subscription.objects.select_related("company").order_by("-updated_at")
        return write_csv_response(
            "cardbook-subscriptions.csv",
            ["ID", "Empresa", "Plan", "Estado", "Monto", "Intervalo", "MRR", "Stripe Customer", "Stripe Subscription", "Renovacion"],
            [
                [
                    subscription.id,
                    subscription.company.name,
                    subscription.plan,
                    subscription.status,
                    subscription.unit_amount,
                    subscription.billing_interval,
                    subscription.normalized_mrr,
                    subscription.stripe_customer_id,
                    subscription.stripe_subscription_id,
                    subscription.current_period_end or "",
                ]
                for subscription in subscriptions
            ],
        )

    def companies_csv(self):
        companies = Company.objects.select_related("owner").prefetch_related("subscriptions").order_by("name")
        rows = []
        for company in companies:
            subscription = company.subscriptions.order_by("-updated_at").first()
            rows.append([
                company.id,
                company.name,
                company.owner.email,
                company.email or "",
                subscription.plan if subscription else "",
                subscription.status if subscription else "sin_plan",
                subscription.normalized_mrr if subscription else 0,
                company.created_at.isoformat(),
            ])
        return write_csv_response(
            "cardbook-companies.csv",
            ["ID", "Empresa", "Owner", "Email", "Plan", "Estado", "MRR", "Registro"],
            rows,
        )


class AgentOverviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        agent = AgentProfile.objects.filter(user=request.user).first()
        if not agent:
            return success_response("Agent overview retrieved successfully.", {
                "clicks": 0,
                "commissions": [],
                "commission_pending": 0,
                "commission_paid": 0,
            })
        commissions = Commission.objects.filter(agent=agent)
        return success_response("Agent overview retrieved successfully.", {
            "clicks": ReferralClick.objects.filter(agent=agent).count(),
            "commissions": CommissionSerializer(commissions[:50], many=True).data,
            "commission_pending": sum((c.commission_amount for c in commissions.filter(status=Commission.STATUS_PENDING)), 0),
            "commission_paid": sum((c.commission_amount for c in commissions.filter(status=Commission.STATUS_PAID)), 0),
        })


class AgentReferralsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        agent = AgentProfile.objects.filter(user=request.user).first()
        return paginate(request, ReferralClick.objects.filter(agent=agent) if agent else ReferralClick.objects.none(), ReferralClickSerializer)


class AgentCommissionsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        agent = AgentProfile.objects.filter(user=request.user).first()
        return paginate(request, Commission.objects.filter(agent=agent) if agent else Commission.objects.none(), CommissionSerializer)


class AgentCommissionPaymentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        agent = AgentProfile.objects.filter(user=request.user).first()
        return paginate(request, CommissionPayment.objects.filter(agent=agent) if agent else CommissionPayment.objects.none(), CommissionPaymentSerializer)


class BillingSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company_id = request.query_params.get("company")
        queryset = Subscription.objects.select_related("company")
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        queryset = [subscription for subscription in queryset if can_view_company_billing(request.user, subscription.company)]
        return success_response("Company subscriptions retrieved successfully.", SubscriptionSerializer(queryset, many=True).data)


class BillingInvoicesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = [invoice for invoice in Invoice.objects.select_related("company", "subscription") if can_view_company_billing(request.user, invoice.company)]
        return success_response("Company invoices retrieved successfully.", InvoiceSerializer(invoices, many=True).data)


class CustomerPortalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        company_id = request.data.get("company") or request.data.get("company_id")
        if not company_id:
            return error_response("company_id is required.", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_view_company_billing(request.user, company):
            return error_response("You do not have permission to open billing for this company.", status_code=status.HTTP_403_FORBIDDEN)
        try:
            session = create_customer_portal_session(
                company=company,
                request=request,
                return_url=request.data.get("return_url", ""),
            )
        except FinanceValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except FinanceConfigurationError as exc:
            return error_response(str(exc), {"configured": False}, status.HTTP_503_SERVICE_UNAVAILABLE)
        return success_response("Customer portal session created.", {
            "configured": True,
            "url": session.url,
            "session_id": getattr(session, "id", ""),
        })


class StripeWebhookAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_payload = request.body
        webhook_secret = get_stripe_webhook_secret()
        if webhook_secret:
            signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
            if not verify_stripe_signature(raw_payload, signature, webhook_secret):
                return error_response("Invalid Stripe signature.", status_code=status.HTTP_400_BAD_REQUEST)
        payload = parse_stripe_payload(raw_payload)
        if payload is None:
            return error_response("Invalid Stripe payload.", status_code=status.HTTP_400_BAD_REQUEST)
        event_id = payload.get("id")
        event_type = payload.get("type")
        if not event_id or not event_type:
            return error_response("Invalid Stripe event.", status_code=status.HTTP_400_BAD_REQUEST)
        result = process_stripe_webhook(event_id, event_type, payload)
        return success_response("Stripe webhook received.", result)
