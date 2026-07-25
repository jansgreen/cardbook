import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView
from rest_framework import generics, permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response
from companies.models import Company
from .models import AgentApplication, AgentCardSale, AgentProfile, Commission, Referral, ReferralInvitation, ReferralNotification
from .permissions import IsAdminUser, IsAgentUser
from .serializers import (
    AgentApplicationSerializer,
    AgentInviteSerializer,
    AgentProfileSerializer,
    CommissionSerializer,
    GenerateCommissionSerializer,
    ReferralNotificationSerializer,
    ReferralInvitationSerializer,
    ReferralSerializer,
    RegisterSourceSerializer,
)
from .services import (
    admin_stats,
    agent_stats,
    approve_commission,
    build_referral_link,
    generate_commission,
    get_agent_by_code,
    mark_user_notifications_read,
    mark_commission_paid,
    register_referral_source,
    unread_notification_count,
)


class AgentInviteAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AgentInviteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Agent invitation failed.", serializer.errors)
        invitation = serializer.save()
        return success_response(
            "Agent invitation created.",
            ReferralInvitationSerializer(invitation, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class AgentMeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        agent = getattr(request.user, "agent_profile", None)
        if not agent:
            return error_response("Agent profile not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Agent profile retrieved.", AgentProfileSerializer(agent, context={"request": request}).data)


class AgentLinkAPIView(APIView):
    permission_classes = [IsAgentUser]

    def get(self, request):
        agent = request.user.agent_profile
        return success_response("Referral link retrieved.", {
            "agent_id": agent.agent_id,
            "referral_code": agent.referral_code,
            "referral_link": build_referral_link(request, agent),
        })


class RegisterSourceAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSourceSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Referral source registration failed.", serializer.errors)
        code = serializer.validated_data["referral_code"]
        agent = get_agent_by_code(code)
        if not agent:
            return error_response("Referral code is invalid or inactive.", status_code=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_authenticated:
            return success_response("Referral code is valid.", {
                "referral_code": agent.referral_code,
                "agent_id": agent.agent_id,
            })
        try:
            referral = register_referral_source(
                user=request.user,
                referral_code=code,
                request=request,
                source_url=serializer.validated_data.get("source_url", ""),
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Referral source registered.", ReferralSerializer(referral).data)


class AgentApplicationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AgentApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Agent application failed.", serializer.errors)
        application = serializer.save()
        return success_response(
            "Agent application submitted.",
            AgentApplicationSerializer(application, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class MyReferralsAPIView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [IsAgentUser]

    def get_queryset(self):
        return Referral.objects.filter(agent=self.request.user.agent_profile).select_related("referred_user", "referred_company", "agent")


class CommissionListAPIView(generics.ListAPIView):
    serializer_class = CommissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Commission.objects.select_related("agent", "company")
        agent = getattr(self.request.user, "agent_profile", None)
        if not agent:
            return Commission.objects.none()
        return Commission.objects.filter(agent=agent).select_related("agent", "company")


class CommissionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CommissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Commission.objects.select_related("agent", "company")
        agent = getattr(self.request.user, "agent_profile", None)
        if not agent:
            return Commission.objects.none()
        return Commission.objects.filter(agent=agent).select_related("agent", "company")


class CommissionApproveAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        commission = get_object_or_404(Commission, pk=pk)
        try:
            approve_commission(commission=commission, approved_by=request.user)
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Commission approved.", CommissionSerializer(commission).data)


class CommissionMarkPaidAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        commission = get_object_or_404(Commission, pk=pk)
        try:
            mark_commission_paid(commission=commission, paid_by=request.user)
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Commission marked as paid.", CommissionSerializer(commission).data)


class GenerateCommissionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = GenerateCommissionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Commission generation failed.", serializer.errors)
        company = get_object_or_404(Company, pk=serializer.validated_data["company_id"])
        commission = generate_commission(
            company=company,
            plan_name=serializer.validated_data["plan_name"],
            payment_amount=serializer.validated_data["payment_amount"],
            payment_reference=serializer.validated_data.get("payment_reference", ""),
            currency=serializer.validated_data.get("currency", "USD"),
        )
        if not commission:
            return error_response("This company has no active referral agent.", status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Commission generated.", CommissionSerializer(commission).data, status.HTTP_201_CREATED)


class AdminAgentListAPIView(generics.ListAPIView):
    serializer_class = AgentProfileSerializer
    permission_classes = [IsAdminUser]
    queryset = AgentProfile.objects.select_related("user").all()


class AdminReferralListAPIView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [IsAdminUser]
    queryset = Referral.objects.select_related("agent", "referred_user", "referred_company").all()


class AdminCommissionListAPIView(generics.ListAPIView):
    serializer_class = CommissionSerializer
    permission_classes = [IsAdminUser]
    queryset = Commission.objects.select_related("agent", "company").all()


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = ReferralNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ReferralNotification.objects.filter(recipient=self.request.user)
        unread = self.request.query_params.get("unread")
        if unread in {"1", "true", "yes"}:
            queryset = queryset.filter(read_at__isnull=True)
        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()[:50]
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Notifications retrieved.", {
            "unread_count": unread_notification_count(request.user),
            "results": serializer.data,
        })


class NotificationMarkReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        updated = mark_user_notifications_read(request.user, notification_id=pk)
        return success_response("Notifications marked as read.", {
            "updated": updated,
            "unread_count": unread_notification_count(request.user),
        })


class ReferralDashboardView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "referrals/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = getattr(self.request.user, "agent_profile", None)
        application = AgentApplication.objects.filter(email__iexact=self.request.user.email).first()
        context["agent"] = agent
        context["agent_application"] = application
        context["is_referral_admin"] = self.request.user.is_staff
        context["admin_stats"] = admin_stats() if self.request.user.is_staff else None
        context["agent_stats"] = agent_stats(agent) if agent else None
        context["referral_link"] = build_referral_link(self.request, agent) if agent else ""
        context["my_referrals"] = Referral.objects.filter(agent=agent).select_related("referred_user", "referred_company")[:10] if agent else []
        context["my_commissions"] = Commission.objects.filter(agent=agent).select_related("company")[:10] if agent else []
        context["my_card_sales"] = AgentCardSale.objects.filter(agent=agent).select_related("company", "commission")[:10] if agent else []
        context["admin_agents"] = AgentProfile.objects.select_related("user").annotate(referral_total=Count("referrals"))[:12] if self.request.user.is_staff else []
        context["admin_commissions"] = Commission.objects.select_related("agent", "company")[:12] if self.request.user.is_staff else []
        context["admin_card_sales"] = AgentCardSale.objects.select_related("agent", "company", "created_by")[:12] if self.request.user.is_staff else []
        return context


class NotificationInboxView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "dashboard/notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = ReferralNotification.objects.filter(recipient=self.request.user).order_by("-created_at")
        context["notifications"] = notifications[:80]
        context["unread_count"] = notifications.filter(read_at__isnull=True).count()
        context["event_types"] = ReferralNotification.TYPE_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get("notification_id")
        mark_user_notifications_read(request.user, notification_id=notification_id)
        return redirect("dashboard-notifications")


class ReferralReportCSVView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        if not request.user.is_staff:
            return redirect("dashboard-referrals")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="cardbook-referrals.csv"'
        writer = csv.writer(response)
        writer.writerow(["Agent", "Referral Code", "User", "Company", "Created"])
        for referral in Referral.objects.select_related("agent", "referred_user", "referred_company"):
            writer.writerow([
                referral.agent.agent_id,
                referral.referral_code,
                referral.referred_user.email,
                referral.referred_company.name if referral.referred_company else "",
                referral.created_at.isoformat(),
            ])
        return response
