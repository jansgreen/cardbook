from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from companies.permissions import get_company_role
from memberships.models import CompanyMember
from .forms import AccessGroupForm, AccessPermissionForm, AccessRoleForm, MemberInviteForm, UserAccessGrantForm
from .models import AccessGroup, AccessPermission, AccessRole, UserAccessGrant
from .permissions import AccessControlRequiredMixin, user_can_manage_access_catalog
from .services import assignable_roles_for, can_manage_member, manageable_companies_for


class DashboardAccessControlView(LoginRequiredMixin, AccessControlRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "dashboard/accesscontrol/index.html"

    def get_companies(self):
        return manageable_companies_for(self.request.user)

    def get_active_company(self):
        companies = self.get_companies()
        company_id = self.request.GET.get("company") or self.request.POST.get("company")
        if company_id:
            company = companies.filter(pk=company_id).first()
            if company:
                return company
        return companies.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_company = self.get_active_company()
        members = CompanyMember.objects.none()
        if active_company:
            members = CompanyMember.objects.filter(company=active_company, is_active=True).select_related("user")
            for member in members:
                member.can_be_managed_by_current_user = can_manage_member(self.request.user, member)
        context.update({
            "companies": self.get_companies(),
            "active_company": active_company,
            "members": members,
            "invite_form": kwargs.get("invite_form") or MemberInviteForm(user=self.request.user, initial={"company": active_company}),
            "permission_form": kwargs.get("permission_form") or AccessPermissionForm(),
            "role_form": kwargs.get("role_form") or AccessRoleForm(),
            "group_form": kwargs.get("group_form") or AccessGroupForm(),
            "grant_form": kwargs.get("grant_form") or UserAccessGrantForm(user=self.request.user, initial={"company": active_company}),
            "access_permissions": AccessPermission.objects.all(),
            "access_roles": AccessRole.objects.prefetch_related("permissions").all(),
            "access_groups": AccessGroup.objects.prefetch_related("roles", "permissions").all(),
            "access_grants": UserAccessGrant.objects.filter(company__in=self.get_companies()).select_related("user", "company", "role", "group"),
            "current_role": get_company_role(self.request.user, active_company) if active_company else None,
            "can_manage_access_catalog": user_can_manage_access_catalog(self.request.user, active_company),
            "assignable_roles": assignable_roles_for(self.request.user, active_company) if active_company else [],
            "role_options": [
                (role, label)
                for role, label in CompanyMember.ROLE_CHOICES
                if active_company and role in assignable_roles_for(self.request.user, active_company)
            ],
            "role_labels": dict(CompanyMember.ROLE_CHOICES),
            "permission_rows": [
                ("Owner", "Control total, facturacion, empresas, miembros y eliminacion."),
                ("Admin", "Gestiona miembros no admin, tarjetas, publicaciones, alianzas y website."),
                ("Manager", "Trabaja con contenido operativo y tarjetas de la empresa."),
                ("Staff", "Puede crear y mantener su propio perfil/tarjeta dentro de la empresa."),
            ],
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        active_company = self.get_active_company()
        if not active_company:
            messages.error(request, "Selecciona una empresa.")
            return redirect("dashboard-access-control")
        can_manage_catalog = user_can_manage_access_catalog(request.user, active_company)

        if action == "invite":
            form = MemberInviteForm(request.POST, user=request.user)
            if form.is_valid():
                member = form.save()
                messages.success(request, f"{member.user.get_full_name() or member.user.username} agregado como {member.get_role_display()}.")
                return redirect(f"{reverse('dashboard-access-control')}?company={member.company_id}")
            return self.render_to_response(self.get_context_data(invite_form=form))

        if action == "create_permission":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para crear permisos globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            form = AccessPermissionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Permiso creado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(permission_form=form))

        if action == "update_permission":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para actualizar permisos globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            permission = get_object_or_404(AccessPermission, pk=request.POST.get("permission_id"))
            form = AccessPermissionForm(request.POST, instance=permission)
            if form.is_valid():
                form.save()
                messages.success(request, "Permiso actualizado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(permission_form=form))

        if action == "create_role":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para crear roles globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            form = AccessRoleForm(request.POST)
            if form.is_valid():
                role = form.save()
                messages.success(request, f"Rol {role.name} creado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(role_form=form))

        if action == "update_role_dynamic":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para actualizar roles globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            role = get_object_or_404(AccessRole, pk=request.POST.get("role_id"))
            form = AccessRoleForm(request.POST, instance=role)
            if form.is_valid():
                form.save()
                messages.success(request, "Rol actualizado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(role_form=form))

        if action == "create_group":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para crear grupos globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            form = AccessGroupForm(request.POST)
            if form.is_valid():
                group = form.save()
                messages.success(request, f"Grupo {group.name} creado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(group_form=form))

        if action == "update_group":
            if not can_manage_catalog:
                messages.error(request, "No tienes permiso para actualizar grupos globales.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            group = get_object_or_404(AccessGroup, pk=request.POST.get("group_id"))
            form = AccessGroupForm(request.POST, instance=group)
            if form.is_valid():
                form.save()
                messages.success(request, "Grupo actualizado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
            return self.render_to_response(self.get_context_data(group_form=form))

        if action == "create_grant":
            form = UserAccessGrantForm(request.POST, user=request.user)
            if form.is_valid():
                grant = form.save()
                messages.success(request, f"Acceso asignado a {grant.user.get_full_name() or grant.user.username}.")
                return redirect(f"{reverse('dashboard-access-control')}?company={grant.company_id}")
            return self.render_to_response(self.get_context_data(grant_form=form))

        if action == "update_grant":
            grant = get_object_or_404(UserAccessGrant, pk=request.POST.get("grant_id"), company__in=self.get_companies())
            form = UserAccessGrantForm(request.POST, user=request.user, instance=grant)
            if form.is_valid():
                grant = form.save()
                messages.success(request, "Acceso actualizado.")
                return redirect(f"{reverse('dashboard-access-control')}?company={grant.company_id}")
            return self.render_to_response(self.get_context_data(grant_form=form))

        if action == "deactivate_grant":
            grant = get_object_or_404(UserAccessGrant, pk=request.POST.get("grant_id"), company__in=self.get_companies())
            grant.is_active = False
            grant.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Acceso desactivado.")
            return redirect(f"{reverse('dashboard-access-control')}?company={grant.company_id}")

        member = get_object_or_404(CompanyMember.objects.select_related("company", "user"), pk=request.POST.get("member_id"), company=active_company)
        if not can_manage_member(request.user, member):
            messages.error(request, "No puedes modificar este miembro.")
            return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")

        if action == "update_role":
            role = request.POST.get("role")
            if role not in assignable_roles_for(request.user, active_company):
                messages.error(request, "Tu rol no permite asignar ese acceso.")
            else:
                member.role = role
                member.save(update_fields=["role"])
                messages.success(request, "Rol actualizado.")
        elif action == "deactivate":
            member.is_active = False
            member.save(update_fields=["is_active"])
            messages.success(request, "Miembro desactivado.")

        return redirect(f"{reverse('dashboard-access-control')}?company={active_company.id}")
