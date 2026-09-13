from django.urls import NoReverseMatch, reverse

from accesscontrol.services import PERM_MANAGE_PLATFORM_USERS, PERM_MANAGE_STRIPE_CONFIGURATION, user_has_access_permission
from companies.models import Company


SECTION_HOME = "home"
SECTION_COMPANIES = "companies"
SECTION_WEBSITE = "website"
SECTION_FORMS = "forms"
SECTION_AI_AGENTS = "ai_agents"
SECTION_CARDS = "cards"
SECTION_BUSINESS_CARDS = "business_cards"
SECTION_ANALYTICS = "analytics"
SECTION_BOOK = "book"
SECTION_NOTIFICATIONS = "notifications"
SECTION_WHITE_CARD_JOB = "white_card_job"
SECTION_REFERRALS = "referrals"
SECTION_ACCESS = "access"
SECTION_FINANCE = "finance"
SECTION_PUBLIC_SITE = "public_site"
SECTION_USERS = "users"
SECTION_STRIPE_CONFIGURATION = "stripe_configuration"


ALL_DASHBOARD_SECTIONS = {
    SECTION_HOME,
    SECTION_COMPANIES,
    SECTION_WEBSITE,
    SECTION_FORMS,
    SECTION_AI_AGENTS,
    SECTION_CARDS,
    SECTION_BUSINESS_CARDS,
    SECTION_ANALYTICS,
    SECTION_BOOK,
    SECTION_NOTIFICATIONS,
    SECTION_WHITE_CARD_JOB,
    SECTION_REFERRALS,
    SECTION_ACCESS,
    SECTION_FINANCE,
    SECTION_PUBLIC_SITE,
    SECTION_USERS,
    SECTION_STRIPE_CONFIGURATION,
}


COMPANY_SECTIONS = {
    SECTION_HOME,
    SECTION_COMPANIES,
    SECTION_WEBSITE,
    SECTION_FORMS,
    SECTION_AI_AGENTS,
    SECTION_CARDS,
    SECTION_BUSINESS_CARDS,
    SECTION_ANALYTICS,
    SECTION_BOOK,
    SECTION_NOTIFICATIONS,
    SECTION_PUBLIC_SITE,
}


JOB_SECTIONS = {
    SECTION_COMPANIES,
    SECTION_WHITE_CARD_JOB,
    SECTION_NOTIFICATIONS,
    SECTION_BOOK,
}


AGENT_SECTIONS = ALL_DASHBOARD_SECTIONS - {SECTION_ACCESS, SECTION_FINANCE}


URL_SECTION_RULES = [
    ("finance-", SECTION_FINANCE),
    ("dashboard-stripe-configuration", SECTION_STRIPE_CONFIGURATION),
    ("dashboard-users", SECTION_USERS),
    ("dashboard-user-", SECTION_USERS),
    ("dashboard-access-control", SECTION_ACCESS),
    ("dashboard-referrals", SECTION_REFERRALS),
    ("dashboard-notifications", SECTION_NOTIFICATIONS),
    ("dashboard-white-card-job", SECTION_WHITE_CARD_JOB),
    ("dashboard-jobcard-", SECTION_WHITE_CARD_JOB),
    ("dashboard-book", SECTION_BOOK),
    ("dashboard-ai-agents", SECTION_AI_AGENTS),
    ("dashboard-company-website", SECTION_WEBSITE),
    ("dashboard-form-builder", SECTION_FORMS),
    ("dashboard-form-field", SECTION_FORMS),
    ("dashboard-business-card", SECTION_BUSINESS_CARDS),
    ("dashboard-business-cards", SECTION_BUSINESS_CARDS),
    ("dashboard-card", SECTION_CARDS),
    ("dashboard-cards", SECTION_CARDS),
    ("dashboard-analytics", SECTION_ANALYTICS),
    ("dashboard-company", SECTION_COMPANIES),
    ("dashboard-companies", SECTION_COMPANIES),
    ("dashboard-home", SECTION_HOME),
]


MENU_DEFINITIONS = [
    {
        "key": SECTION_HOME,
        "label": "Resumen",
        "url_name": "dashboard-home",
        "active_sections": [SECTION_HOME],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13h7V4H4v9Zm0 7h7v-5H4v5Zm9 0h7v-9h-7v9Zm0-16v5h7V4h-7Z"/></svg>',
    },
    {
        "key": SECTION_COMPANIES,
        "label": "Empresas",
        "url_name": "dashboard-companies",
        "active_sections": [SECTION_COMPANIES],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21V7l9-4 9 4v14h-6v-6H9v6H3Zm5-10h2V9H8v2Zm0 3h2v-2H8v2Zm6-3h2V9h-2v2Zm0 3h2v-2h-2v2Z"/></svg>',
    },
    {
        "key": SECTION_WEBSITE,
        "label": "Website Builder",
        "company_url_name": "dashboard-company-website",
        "fallback_url_name": "dashboard-companies",
        "active_sections": [SECTION_WEBSITE],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5Zm3-1a1 1 0 0 0-1 1v2h12V5a1 1 0 0 0-1-1H7Zm11 5H6v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9Zm-9 3h6v2H9v-2Zm0 4h4v2H9v-2Z"/></svg>',
    },
    {
        "key": SECTION_FORMS,
        "label": "Forms Builder",
        "company_url_name": "dashboard-form-builder-list",
        "fallback_url_name": "dashboard-companies",
        "active_sections": [SECTION_FORMS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm0 2v14h14V5H5Zm3 3h8v2H8V8Zm0 4h8v2H8v-2Zm0 4h5v2H8v-2Z"/></svg>',
    },
    {
        "key": SECTION_AI_AGENTS,
        "label": "Agentes IA",
        "url_name": "dashboard-ai-agents",
        "active_sections": [SECTION_AI_AGENTS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 1 7 7v1.1a4 4 0 0 1 2 3.5V17a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4v-3.4a4 4 0 0 1 2-3.5V9a7 7 0 0 1 7-7Zm-5 9a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2H7Zm5-7a5 5 0 0 0-5 5h10a5 5 0 0 0-5-5Z"/></svg>',
    },
    {
        "key": SECTION_CARDS,
        "label": "Perfil del negocio",
        "url_name": "dashboard-cards",
        "active_sections": [SECTION_CARDS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm0 4h16V7H4v2Zm3 6h6v-2H7v2Z"/></svg>',
    },
    {
        "key": SECTION_BUSINESS_CARDS,
        "label": "Presentacion",
        "url_name": "dashboard-business-cards",
        "active_sections": [SECTION_BUSINESS_CARDS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5A2.5 2.5 0 0 1 5.5 4h13A2.5 2.5 0 0 1 21 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5v-11Zm3 2v2h7v-2H6Zm0 4v1.6h11.5v-1.6H6Zm0 3.2v1.6h8.5v-1.6H6Z"/></svg>',
    },
    {
        "key": SECTION_ANALYTICS,
        "label": "Estadistica",
        "url_name": "dashboard-analytics",
        "active_sections": [SECTION_ANALYTICS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V10h4v11H5Zm5 0V3h4v18h-4Zm5 0v-7h4v7h-4Z"/></svg>',
    },
    {
        "key": SECTION_BOOK,
        "label": "Book",
        "url_name": "dashboard-book",
        "active_sections": [SECTION_BOOK],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4a3 3 0 0 1 3-3h11v18H8a3 3 0 0 0-3 3V4Zm3-1a1 1 0 0 0-1 1v13.2A4.96 4.96 0 0 1 8 17h9V3H8Zm2 4h5v2h-5V7Zm0 4h5v2h-5v-2Z"/></svg>',
    },
    {
        "key": SECTION_NOTIFICATIONS,
        "label": "Notificaciones",
        "url_name": "dashboard-notifications",
        "active_sections": [SECTION_NOTIFICATIONS],
        "badge_context": "dashboard_unread_notifications",
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22a2.8 2.8 0 0 0 2.7-2h-5.4A2.8 2.8 0 0 0 12 22Zm7-6V10a7 7 0 0 0-5-6.7V2h-4v1.3A7 7 0 0 0 5 10v6l-2 2v1h18v-1l-2-2Z"/></svg>',
    },
    {
        "key": SECTION_WHITE_CARD_JOB,
        "label": "White Card Job",
        "url_name": "dashboard-white-card-job",
        "active_sections": [SECTION_WHITE_CARD_JOB],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v14a2 2 0 0 1-3.1 1.7L12 17.4l-4.9 3.3A2 2 0 0 1 4 19V5Zm3-1a1 1 0 0 0-1 1v14l6-4 6 4V5a1 1 0 0 0-1-1H7Zm2 5h6v2H9V9Zm0 4h4v2H9v-2Z"/></svg>',
    },
    {
        "key": SECTION_REFERRALS,
        "label": "Referidos",
        "url_name": "dashboard-referrals",
        "active_sections": [SECTION_REFERRALS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 11a4 4 0 1 0-3.7-5.5A5.98 5.98 0 0 0 2 10a6 6 0 0 0 10.3 4.2A4 4 0 1 0 16 11Zm-8 3a4 4 0 1 1 3.3-6.3A4 4 0 0 0 12 11c0 .6.1 1.1.4 1.6A4 4 0 0 1 8 14Z"/></svg>',
    },
    {
        "key": SECTION_ACCESS,
        "label": "Accesos",
        "url_name": "dashboard-access-control",
        "active_sections": [SECTION_ACCESS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 10 4.6-.6 8-5 8-10V5l-8-3Zm0 3.1 5 1.9v4c0 3.7-2.1 6.8-5 7.8-2.9-1-5-4.1-5-7.8V7l5-1.9Z"/></svg>',
    },
    {
        "key": SECTION_FINANCE,
        "label": "Finanzas",
        "url_name": "finance-dashboard",
        "active_sections": [SECTION_FINANCE],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm0 4h16V6H4v2Zm3 4v2h5v-2H7Zm0 4v2h9v-2H7Z"/></svg>',
    },
    {
        "key": SECTION_USERS,
        "label": "Usuarios",
        "url_name": "dashboard-users",
        "active_sections": [SECTION_USERS],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 11a4 4 0 1 0-3.7-5.5A5.98 5.98 0 0 0 2 10a6 6 0 0 0 10.3 4.2A4 4 0 1 0 16 11Zm-8 3a4 4 0 1 1 3.3-6.3A4 4 0 0 0 12 11c0 .6.1 1.1.4 1.6A4 4 0 0 1 8 14Zm8 5a3 3 0 0 1 6 0v1H10v-1a6 6 0 0 1 6-6c1.1 0 2.1.3 3 .8A4.95 4.95 0 0 0 16 19Z"/></svg>',
    },
    {
        "key": SECTION_STRIPE_CONFIGURATION,
        "label": "Stripe",
        "url_name": "dashboard-stripe-configuration",
        "active_sections": [SECTION_STRIPE_CONFIGURATION],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V6Zm2 3h12V6a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1v3Zm0 2v7a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-7H6Zm2 4h5v2H8v-2Z"/></svg>',
    },
    {
        "key": SECTION_PUBLIC_SITE,
        "label": "Sitio publico",
        "url_name": "web-home",
        "active_sections": [SECTION_PUBLIC_SITE],
        "icon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.9 9h-3.1a15.8 15.8 0 0 0-1.1-5 8.1 8.1 0 0 1 4.2 5ZM12 4.1c.8 1.1 1.5 3.1 1.8 5H10.2c.3-1.9 1-3.9 1.8-5ZM4.3 13h3.5c.1 1.8.5 3.5 1.1 4.9A8 8 0 0 1 4.3 13Z"/></svg>',
    },
]


def dashboard_user_type(user):
    if not user or not user.is_authenticated:
        return ""
    if user.is_superuser:
        return "superuser"
    if getattr(user, "registration_intent", "") == "agent" or hasattr(user, "agent_profile"):
        return "agent"
    if getattr(user, "registration_intent", "") == "job":
        return "job"
    return "company"


def allowed_dashboard_sections(user):
    user_type = dashboard_user_type(user)
    if user_type == "superuser":
        return set(ALL_DASHBOARD_SECTIONS)
    if user_type == "agent":
        return set(AGENT_SECTIONS)
    if user_type == "job":
        return set(JOB_SECTIONS)
    if user_type == "company":
        return set(COMPANY_SECTIONS)
    return set()


def section_for_url_name(url_name):
    if not url_name:
        return None
    for prefix, section in URL_SECTION_RULES:
        if url_name == prefix or url_name.startswith(prefix):
            return section
    return None


def can_access_dashboard_section(user, section):
    if not section:
        return True
    if section == SECTION_USERS:
        return bool(user and user.is_authenticated and (user.is_superuser or user_has_access_permission(user, PERM_MANAGE_PLATFORM_USERS)))
    if section == SECTION_STRIPE_CONFIGURATION:
        return bool(user and user.is_authenticated and (user.is_superuser or user_has_access_permission(user, PERM_MANAGE_STRIPE_CONFIGURATION)))
    return section in allowed_dashboard_sections(user)


def first_active_company_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
    ).distinct().first()


def build_menu_url(item, active_company=None):
    if item.get("company_url_name"):
        if active_company:
            try:
                return reverse(item["company_url_name"], kwargs={"company_id": active_company.id})
            except NoReverseMatch:
                pass
        return reverse(item["fallback_url_name"])
    return reverse(item["url_name"])


def default_dashboard_url_name(user):
    user_type = dashboard_user_type(user)
    if user_type == "job":
        return "dashboard-white-card-job"
    if user_type == "agent":
        return "dashboard-referrals"
    return "dashboard-home"


def default_dashboard_url(user):
    return reverse(default_dashboard_url_name(user))


def dashboard_menu_for_user(user, current_section=None, active_company=None):
    allowed_sections = allowed_dashboard_sections(user)
    if not active_company:
        active_company = first_active_company_for_user(user)
    menu = []
    for item in MENU_DEFINITIONS:
        if item["key"] == SECTION_USERS:
            if user and user.is_authenticated and (user.is_superuser or user_has_access_permission(user, PERM_MANAGE_PLATFORM_USERS)):
                menu.append({
                    **item,
                    "url": build_menu_url(item, active_company=active_company),
                    "is_active": current_section in item.get("active_sections", []),
                })
            continue
        if item["key"] == SECTION_STRIPE_CONFIGURATION:
            if user and user.is_authenticated and (user.is_superuser or user_has_access_permission(user, PERM_MANAGE_STRIPE_CONFIGURATION)):
                menu.append({
                    **item,
                    "url": build_menu_url(item, active_company=active_company),
                    "is_active": current_section in item.get("active_sections", []),
                })
            continue
        if item["key"] not in allowed_sections:
            continue
        menu.append({
            **item,
            "url": build_menu_url(item, active_company=active_company),
            "is_active": current_section in item.get("active_sections", []),
        })
    return menu
