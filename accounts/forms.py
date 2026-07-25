from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile


class WebLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Usuario"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contrasena"}),
    )


class WebRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@empresa.com"}),
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
    )

    class Meta:
        model = Profile
        fields = ("username", "email", "first_name", "last_name", "phone_number", "preferred_language")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de usuario"}),
            "preferred_language": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Contrasena segura"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirma la contrasena"})


class RegistrationIntentForm(forms.Form):
    usage = forms.ChoiceField(
        choices=Profile.INTENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "registration-intent-options"}),
    )
    referral_code = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Codigo de referido de agente"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        usage = cleaned_data.get("usage")
        referral_code = (cleaned_data.get("referral_code") or "").strip()
        if usage == Profile.INTENT_AGENT and referral_code:
            from referrals.services import get_agent_by_code

            if not get_agent_by_code(referral_code):
                self.add_error("referral_code", "Este codigo de referido no existe o no esta activo.")
        cleaned_data["referral_code"] = referral_code
        return cleaned_data


class AgentApplicationForm(forms.Form):
    full_name = forms.CharField(
        max_length=180,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
    )
    phone_number = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
    )
    city = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ciudad"}),
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Cuentanos tu experiencia vendiendo, creando redes o atendiendo negocios."}),
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Por que quieres ser agente de Cardbook?"}),
    )
