from memberships.models import CompanyMember


def get_company_role(user, company):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return CompanyMember.ROLE_OWNER
    if company.owner_id == user.id:
        return CompanyMember.ROLE_OWNER
    membership = CompanyMember.objects.filter(company=company, user=user, is_active=True).first()
    return membership.role if membership else None


def can_access_company(user, company):
    if user and user.is_authenticated and user.is_superuser:
        return True
    return get_company_role(user, company) in {
        CompanyMember.ROLE_OWNER,
        CompanyMember.ROLE_ADMIN,
        CompanyMember.ROLE_MANAGER,
        CompanyMember.ROLE_STAFF,
    }


def can_manage_company(user, company):
    if user and user.is_authenticated and user.is_superuser:
        return True
    return get_company_role(user, company) in {
        CompanyMember.ROLE_OWNER,
        CompanyMember.ROLE_ADMIN,
    }
