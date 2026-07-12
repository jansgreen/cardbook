from django import forms

from accounts.models import Profile
from companies.models import Company
from memberships.models import CompanyMember
from .models import AccessGroup, AccessPermission, AccessRole, UserAccessGrant
from .services import assignable_roles_for, manageable_companies_for


class MemberInviteForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Company.objects.none(), widget=forms.Select(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "usuario@email.com"}))
    role = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-control"}))

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = manageable_companies_for(user)
        self.fields["company"].label = "Empresa"
        self.fields["email"].label = "Email del usuario"
        self.fields["role"].label = "Rol"
        role_labels = dict(CompanyMember.ROLE_CHOICES)
        self.fields["role"].choices = [
            (role, role_labels[role])
            for role, _label in CompanyMember.ROLE_CHOICES
            if role != CompanyMember.ROLE_OWNER
        ]

    def clean_company(self):
        company = self.cleaned_data["company"]
        if company not in manageable_companies_for(self.user):
            raise forms.ValidationError("No tienes permiso para administrar esta empresa.")
        return company

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user = Profile.objects.filter(email__iexact=email).first()
        if not user:
            raise forms.ValidationError("No existe un usuario registrado con ese email.")
        if user == self.user:
            raise forms.ValidationError("No puedes agregarte a ti mismo.")
        self.target_user = user
        return email

    def clean(self):
        cleaned = super().clean()
        company = cleaned.get("company")
        role = cleaned.get("role")
        if company and role and role not in assignable_roles_for(self.user, company):
            raise forms.ValidationError("Tu rol no permite asignar ese nivel de acceso.")
        return cleaned

    def save(self):
        company = self.cleaned_data["company"]
        role = self.cleaned_data["role"]
        member, _ = CompanyMember.objects.update_or_create(
            company=company,
            user=self.target_user,
            defaults={"role": role, "is_active": True},
        )
        return member


class AccessPermissionForm(forms.ModelForm):
    code = forms.RegexField(
        regex=r"^[a-z0-9_.-]+$",
        error_messages={"invalid": "Usa solo minusculas, numeros, puntos, guiones y guiones bajos."},
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "cards.create_business_card.cardbook"}),
    )

    class Meta:
        model = AccessPermission
        fields = ["code", "name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Crear tarjetas bajo Cardbook"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AccessRoleForm(forms.ModelForm):
    class Meta:
        model = AccessRole
        fields = ["name", "description", "permissions", "is_agent_role", "default_commission_percent", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Agente Cardbook"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "permissions": forms.CheckboxSelectMultiple(),
            "is_agent_role": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_commission_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = AccessPermission.objects.filter(is_active=True)


class AccessGroupForm(forms.ModelForm):
    class Meta:
        model = AccessGroup
        fields = ["name", "description", "roles", "permissions", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Equipo de agentes"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "roles": forms.CheckboxSelectMultiple(),
            "permissions": forms.CheckboxSelectMultiple(),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roles"].queryset = AccessRole.objects.filter(is_active=True)
        self.fields["permissions"].queryset = AccessPermission.objects.filter(is_active=True)


class UserAccessGrantForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "agente@email.com"}))

    class Meta:
        model = UserAccessGrant
        fields = ["company", "email", "role", "group", "commission_percent", "notes", "is_active"]
        widgets = {
            "company": forms.Select(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "group": forms.Select(attrs={"class": "form-control"}),
            "commission_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Notas internas del acceso o acuerdo comercial"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.request_user = user
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = manageable_companies_for(user)
        self.fields["role"].queryset = AccessRole.objects.filter(is_active=True)
        self.fields["group"].queryset = AccessGroup.objects.filter(is_active=True)
        self.fields["group"].required = False
        if self.instance.pk:
            self.fields["email"].initial = self.instance.user.email

    def clean_company(self):
        company = self.cleaned_data["company"]
        if company not in manageable_companies_for(self.request_user):
            raise forms.ValidationError("No tienes permiso para administrar accesos en esta empresa.")
        return company

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user = Profile.objects.filter(email__iexact=email).first()
        if not user:
            raise forms.ValidationError("No existe un usuario registrado con ese email.")
        self.target_user = user
        return email

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.target_user
        if instance.commission_percent is None:
            instance.commission_percent = instance.role.default_commission_percent
        if commit:
            if self.instance.pk:
                instance.save()
            else:
                instance, _ = UserAccessGrant.objects.update_or_create(
                    user=instance.user,
                    company=instance.company,
                    role=instance.role,
                    defaults={
                        "group": instance.group,
                        "commission_percent": instance.commission_percent,
                        "notes": instance.notes,
                        "is_active": instance.is_active,
                    },
                )
            self.instance = instance
        return instance
