from django.contrib import messages
from django.shortcuts import redirect

from .models import UserAccessGrant
from .services import PERM_MANAGE_ACCESS_CONTROL, ensure_default_permissions, manageable_companies_for


class AccessControlRequiredMixin:
    access_denied_message = "No tienes permisos para administrar accesos."
    access_denied_redirect = "dashboard-home"

    def dispatch(self, request, *args, **kwargs):
        ensure_default_permissions()
        if not user_can_manage_accesses(request.user):
            messages.error(request, self.access_denied_message)
            return redirect(self.access_denied_redirect)
        return super().dispatch(request, *args, **kwargs)


def user_can_manage_accesses(user):
    return manageable_companies_for(user).exists()


def user_can_manage_access_catalog(user, company=None):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    grants = UserAccessGrant.objects.filter(user=user, is_active=True, role__is_active=True)
    if company:
        grants = grants.filter(company=company)
    return (
        grants.filter(role__permissions__code=PERM_MANAGE_ACCESS_CONTROL, role__permissions__is_active=True).exists()
        or grants.filter(group__permissions__code=PERM_MANAGE_ACCESS_CONTROL, group__permissions__is_active=True).exists()
        or grants.filter(group__roles__permissions__code=PERM_MANAGE_ACCESS_CONTROL, group__roles__permissions__is_active=True).exists()
    )
