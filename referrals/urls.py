from django.urls import path

from .views import (
    AdminAgentListAPIView,
    AdminCommissionListAPIView,
    AdminReferralListAPIView,
    AgentInviteAPIView,
    AgentLinkAPIView,
    AgentMeAPIView,
    CommissionApproveAPIView,
    CommissionDetailAPIView,
    CommissionListAPIView,
    CommissionMarkPaidAPIView,
    GenerateCommissionAPIView,
    MyReferralsAPIView,
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    ReferralReportCSVView,
    RegisterSourceAPIView,
)


urlpatterns = [
    path("agent/invite/", AgentInviteAPIView.as_view(), name="api-referral-agent-invite"),
    path("agent/me/", AgentMeAPIView.as_view(), name="api-referral-agent-me"),
    path("agent/link/", AgentLinkAPIView.as_view(), name="api-referral-agent-link"),
    path("register-source/", RegisterSourceAPIView.as_view(), name="api-referral-register-source"),
    path("my-referrals/", MyReferralsAPIView.as_view(), name="api-referral-my-referrals"),
    path("commissions/", CommissionListAPIView.as_view(), name="api-referral-commission-list"),
    path("commissions/generate/", GenerateCommissionAPIView.as_view(), name="api-referral-commission-generate"),
    path("commissions/<int:pk>/", CommissionDetailAPIView.as_view(), name="api-referral-commission-detail"),
    path("commissions/<int:pk>/approve/", CommissionApproveAPIView.as_view(), name="api-referral-commission-approve"),
    path("commissions/<int:pk>/mark-paid/", CommissionMarkPaidAPIView.as_view(), name="api-referral-commission-mark-paid"),
    path("notifications/", NotificationListAPIView.as_view(), name="api-referral-notifications"),
    path("notifications/mark-read/", NotificationMarkReadAPIView.as_view(), name="api-referral-notifications-mark-read"),
    path("notifications/<int:pk>/mark-read/", NotificationMarkReadAPIView.as_view(), name="api-referral-notification-mark-read"),
    path("admin/agents/", AdminAgentListAPIView.as_view(), name="api-referral-admin-agents"),
    path("admin/referrals/", AdminReferralListAPIView.as_view(), name="api-referral-admin-referrals"),
    path("admin/commissions/", AdminCommissionListAPIView.as_view(), name="api-referral-admin-commissions"),
    path("admin/reports/referrals.csv", ReferralReportCSVView.as_view(), name="api-referral-report-csv"),
]
