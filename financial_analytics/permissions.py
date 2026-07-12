from companies.permissions import can_access_company


PERMISSION_MAP = {
    "dashboard": "subscriptions.can_view_financial_dashboard",
    "revenue": "billing.can_view_revenue",
    "subscriptions": "subscriptions.can_view_subscriptions",
    "companies": "subscriptions.can_view_companies_billing",
    "referrals": "referrals.can_view_referrals",
    "commissions": "referrals.can_view_commissions",
    "approve_commissions": "referrals.can_approve_commissions",
    "mark_commissions_paid": "referrals.can_mark_commissions_paid",
    "payments": "billing.can_view_payments",
    "refunds": "billing.can_process_refunds",
    "reports": "referrals.can_export_financial_reports",
    "stripe": "subscriptions.can_access_stripe_dashboard",
}


def has_finance_permission(user, key):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    permission = PERMISSION_MAP.get(key)
    return bool(permission and user.has_perm(permission))


def can_view_company_billing(user, company):
    return has_finance_permission(user, "companies") or can_access_company(user, company)


def can_view_agent_finance(user, agent):
    return user.is_authenticated and (user.is_superuser or user.id == agent.user_id or has_finance_permission(user, "referrals"))
