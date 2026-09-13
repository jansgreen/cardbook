from companies.models import Company
from companies.permissions import can_manage_company, get_company_role
from memberships.models import CompanyMember
from .models import AccessPermission, UserAccessGrant


MANAGER_ROLES = {CompanyMember.ROLE_OWNER, CompanyMember.ROLE_ADMIN}
OWNER_ASSIGNABLE_ROLES = [CompanyMember.ROLE_ADMIN, CompanyMember.ROLE_MANAGER, CompanyMember.ROLE_STAFF]
ADMIN_ASSIGNABLE_ROLES = [CompanyMember.ROLE_MANAGER, CompanyMember.ROLE_STAFF]
PERM_MANAGE_ACCESS_CONTROL = "access.manage"
PERM_CREATE_CARDBOOK_BUSINESS_CARDS = "cards.create_business_card.cardbook"
PERM_MANAGE_WEBSITE_BUILDER = "websitebuilder.manage"
PERM_PUBLISH_WEBSITE_BUILDER = "websitebuilder.publish"
PERM_MANAGE_AI_AGENTS = "ai_agents.manage"
PERM_MANAGE_PLATFORM_USERS = "users.manage"
PERM_MANAGE_STRIPE_CONFIGURATION = "stripe.configure"
PERM_MANAGE_MEMBERSHIP_PLANS = "plans.manage"

DEFAULT_PERMISSIONS = [
    (PERM_MANAGE_ACCESS_CONTROL, "Administrar accesos", "Permite entrar al CRUD de roles, grupos y asignaciones."),
    ("companies.manage_content", "Gestionar contenido empresarial", "Permite operar contenido dentro de empresas asignadas."),
    ("cards.create_profile", "Crear perfiles de negocio", "Permite crear perfiles digitales en empresas asignadas."),
    (PERM_CREATE_CARDBOOK_BUSINESS_CARDS, "Crear tarjetas bajo Cardbook", "Permite crear perfiles y tarjetas de presentacion bajo la empresa Cardbook."),
    (PERM_MANAGE_WEBSITE_BUILDER, "Administrar Website Builder", "Permite crear y editar sitios web empresariales."),
    (PERM_PUBLISH_WEBSITE_BUILDER, "Publicar Website Builder", "Permite publicar o despublicar sitios web empresariales."),
    (PERM_MANAGE_AI_AGENTS, "Administrar agentes IA", "Permite configurar agentes, leads, entrenamiento y conocimiento IA en empresas asignadas."),
    (PERM_MANAGE_PLATFORM_USERS, "Administrar usuarios", "Permite ver, crear, editar y desactivar usuarios registrados en la plataforma."),
    (PERM_MANAGE_STRIPE_CONFIGURATION, "Configurar Stripe", "Permite configurar claves, modo y prices de Stripe para cobros de membresias."),
    (PERM_MANAGE_MEMBERSHIP_PLANS, "Administrar planes", "Permite crear, editar, activar y desactivar planes de membresia y precios."),
    ("sales.earn_commission", "Recibir comision", "Marca al usuario como agente con porcentaje de comision."),
]


def ensure_default_permissions():
    permissions = {}
    for code, name, description in DEFAULT_PERMISSIONS:
        permission, _ = AccessPermission.objects.get_or_create(code=code, defaults={"name": name, "description": description})
        permissions[code] = permission
    from .models import AccessRole

    agent_role, _ = AccessRole.objects.get_or_create(
        name="Agente Cardbook",
        defaults={
            "description": "Agente autorizado para crear tarjetas bajo Cardbook y recibir comision.",
            "is_agent_role": True,
            "default_commission_percent": 15,
        },
    )
    agent_role.permissions.add(
        permissions[PERM_CREATE_CARDBOOK_BUSINESS_CARDS],
        permissions["sales.earn_commission"],
    )
    website_editor_role, _ = AccessRole.objects.get_or_create(
        name="Editor Website Builder",
        defaults={
            "description": "Usuario autorizado para crear, editar y publicar sitios empresariales.",
            "default_commission_percent": 0,
        },
    )
    website_editor_role.permissions.add(
        permissions[PERM_MANAGE_WEBSITE_BUILDER],
        permissions[PERM_PUBLISH_WEBSITE_BUILDER],
    )
    ai_manager_role, _ = AccessRole.objects.get_or_create(
        name="Administrador de agentes IA",
        defaults={
            "description": "Usuario autorizado para entrenar, configurar y revisar agentes IA de empresas asignadas.",
            "default_commission_percent": 0,
        },
    )
    ai_manager_role.permissions.add(permissions[PERM_MANAGE_AI_AGENTS])


def manageable_companies_for(user):
    if not user or not user.is_authenticated:
        return Company.objects.none()
    if user.is_superuser:
        return Company.objects.filter(is_active=True)
    grant_companies = Company.objects.filter(
        is_active=True,
        access_grants__user=user,
        access_grants__is_active=True,
        access_grants__role__permissions__code=PERM_MANAGE_ACCESS_CONTROL,
        access_grants__role__permissions__is_active=True,
    )
    return (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(
            is_active=True,
            members__user=user,
            members__is_active=True,
            members__role__in=MANAGER_ROLES,
        )
        | grant_companies
    ).distinct()


def assignable_roles_for(user, company):
    if user and user.is_authenticated and user.is_superuser:
        return OWNER_ASSIGNABLE_ROLES
    role = get_company_role(user, company)
    if role == CompanyMember.ROLE_OWNER:
        return OWNER_ASSIGNABLE_ROLES
    if role == CompanyMember.ROLE_ADMIN:
        return ADMIN_ASSIGNABLE_ROLES
    return []


def can_manage_member(user, member):
    if user and user.is_authenticated and user.is_superuser:
        return member.role != CompanyMember.ROLE_OWNER or member.company.owner_id != member.user_id
    if not can_manage_company(user, member.company):
        return False
    actor_role = get_company_role(user, member.company)
    if member.role == CompanyMember.ROLE_OWNER:
        return False
    if actor_role == CompanyMember.ROLE_ADMIN and member.role == CompanyMember.ROLE_ADMIN:
        return False
    return True


def user_has_access_permission(user, code, company=None):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if company and can_manage_company(user, company):
        return True
    grants = UserAccessGrant.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
    )
    if company:
        grants = grants.filter(company=company)
    return grants.filter(
        role__permissions__code=code,
        role__permissions__is_active=True,
    ).exists() or grants.filter(
        group__permissions__code=code,
        group__permissions__is_active=True,
    ).exists() or grants.filter(
        group__roles__permissions__code=code,
        group__roles__permissions__is_active=True,
    ).exists()


def cardbook_company():
    return (
        Company.objects.filter(is_active=True, slug__iexact="cardbook").first()
        or Company.objects.filter(is_active=True, name__iexact="Cardbook").first()
        or Company.objects.filter(is_active=True, name__icontains="Cardbook").first()
    )


def companies_for_profile_creation(user):
    if user and user.is_authenticated and user.is_superuser:
        return Company.objects.filter(is_active=True)
    owned_or_member = (
        Company.objects.filter(is_active=True, owner=user)
        | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
    )
    permitted = Company.objects.filter(
        is_active=True,
        access_grants__user=user,
        access_grants__is_active=True,
        access_grants__role__permissions__code__in=["cards.create_profile", PERM_CREATE_CARDBOOK_BUSINESS_CARDS],
    )
    return (owned_or_member | permitted).distinct()
