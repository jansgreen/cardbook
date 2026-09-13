from django import forms

import re
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import password_validation

from accounts.models import Profile
from billing.models import MembershipPlan, StripeConfiguration, ensure_default_membership_plans
from business_feed.models import BusinessPost
from cards.models import BusinessCard, DigitalCard
from cards.services import (
    can_create_profile_for_company,
    can_use_profile_for_business_card,
    profile_creation_companies,
    usable_profiles_for_business_cards,
)
from companies.models import Company
from companies.permissions import can_access_company
from accesscontrol.services import PERM_CREATE_CARDBOOK_BUSINESS_CARDS, user_has_access_permission


WHATSAPP_ALLOWED_HOSTS = {"wa.me", "www.wa.me", "api.whatsapp.com", "web.whatsapp.com"}


class AccountSettingsForm(forms.ModelForm):
    current_password = forms.CharField(
        required=False,
        label="Contrasena actual",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        required=False,
        label="Nueva contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        required=False,
        label="Confirmar nueva contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "preferred_language",
            "avatar",
            "current_password",
            "new_password1",
            "new_password2",
        ]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Email",
            "phone_number": "Telefono",
            "preferred_language": "Idioma preferido",
            "avatar": "Foto de perfil",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@empresa.com"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
            "preferred_language": forms.Select(attrs={"class": "form-control"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if not any([current_password, new_password1, new_password2]):
            return cleaned_data

        if not current_password:
            self.add_error("current_password", "Ingresa tu contrasena actual.")
        elif not self.instance.check_password(current_password):
            self.add_error("current_password", "La contrasena actual no es correcta.")

        if not new_password1:
            self.add_error("new_password1", "Ingresa la nueva contrasena.")
        if not new_password2:
            self.add_error("new_password2", "Confirma la nueva contrasena.")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Las contrasenas no coinciden.")
        if new_password1:
            try:
                password_validation.validate_password(new_password1, self.instance)
            except forms.ValidationError as error:
                self.add_error("new_password1", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_m2m()
        return user


class AccountPlanForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        label="Empresa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    plan = forms.ChoiceField(
        choices=[],
        label="Membresia",
        widget=forms.RadioSelect(attrs={"class": "plan-radio-list"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = (
            Company.objects.filter(is_active=True, owner=user)
            | Company.objects.filter(is_active=True, members__user=user, members__is_active=True)
        ).distinct()
        ensure_default_membership_plans()
        self.plan_queryset = MembershipPlan.objects.filter(is_active=True).order_by("order", "unit_amount", "name")
        self.fields["plan"].choices = [(plan.key, plan.name) for plan in self.plan_queryset]

    def clean_plan(self):
        key = self.cleaned_data["plan"]
        plan = MembershipPlan.objects.filter(key=key, is_active=True).first()
        if not plan:
            raise forms.ValidationError("Selecciona una membresia activa.")
        self.selected_plan = plan
        return key

    def get_selected_plan(self):
        return getattr(self, "selected_plan", None)


class PlatformUserForm(forms.ModelForm):
    password1 = forms.CharField(
        required=False,
        label="Nueva contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        required=False,
        label="Confirmar contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "preferred_language",
            "registration_intent",
            "avatar",
            "is_active",
            "password1",
            "password2",
        ]
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Email",
            "phone_number": "Telefono",
            "preferred_language": "Idioma",
            "registration_intent": "Tipo de cuenta",
            "avatar": "Foto de perfil",
            "is_active": "Usuario activo",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_language": forms.Select(attrs={"class": "form-control"}),
            "registration_intent": forms.Select(attrs={"class": "form-control"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.creating = kwargs.pop("creating", False)
        super().__init__(*args, **kwargs)
        if self.creating:
            self.fields["password1"].required = True
            self.fields["password2"].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if self.creating or password1 or password2:
            if not password1:
                self.add_error("password1", "Ingresa una contrasena.")
            if not password2:
                self.add_error("password2", "Confirma la contrasena.")
            if password1 and password2 and password1 != password2:
                self.add_error("password2", "Las contrasenas no coinciden.")
            if password1:
                try:
                    password_validation.validate_password(password1, self.instance)
                except forms.ValidationError as error:
                    self.add_error("password1", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user


class StripeConfigurationForm(forms.ModelForm):
    secret_key = forms.CharField(
        required=False,
        label="Secret key",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "off", "placeholder": "sk_test_... o sk_live_..."}),
        help_text="Requerida para crear Checkout y cobrar. Si la dejas vacia al editar, se conserva la clave actual.",
    )
    webhook_secret = forms.CharField(
        required=False,
        label="Webhook secret",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "off", "placeholder": "whsec_..."}),
        help_text="Requerida para validar webhooks de Stripe. Si la dejas vacia al editar, se conserva la clave actual.",
    )

    class Meta:
        model = StripeConfiguration
        fields = [
            "mode",
            "is_active",
            "publishable_key",
            "secret_key",
            "webhook_secret",
            "starter_price_id",
            "business_price_id",
            "team_price_id",
        ]
        labels = {
            "mode": "Modo",
            "is_active": "Configuracion activa",
            "publishable_key": "Publishable key",
            "starter_price_id": "Price ID Inicial",
            "business_price_id": "Price ID Negocio",
            "team_price_id": "Price ID Equipo",
        }
        widgets = {
            "mode": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "publishable_key": forms.TextInput(attrs={"class": "form-control", "placeholder": "pk_test_... o pk_live_..."}),
            "starter_price_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "price_..."}),
            "business_price_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "price_..."}),
            "team_price_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "price_..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.secret_key:
                self.fields["secret_key"].widget.attrs["placeholder"] = self.instance.masked_secret_key
            if self.instance.webhook_secret:
                self.fields["webhook_secret"].widget.attrs["placeholder"] = self.instance.masked_webhook_secret

    def clean_publishable_key(self):
        key = (self.cleaned_data.get("publishable_key") or "").strip()
        if key and not key.startswith(("pk_test_", "pk_live_")):
            raise forms.ValidationError("La publishable key debe comenzar con pk_test_ o pk_live_.")
        return key

    def clean_secret_key(self):
        key = (self.cleaned_data.get("secret_key") or "").strip()
        if key and not key.startswith(("sk_test_", "sk_live_")):
            raise forms.ValidationError("La secret key debe comenzar con sk_test_ o sk_live_.")
        if not key and self.instance and self.instance.pk:
            return self.instance.secret_key
        return key

    def clean_webhook_secret(self):
        key = (self.cleaned_data.get("webhook_secret") or "").strip()
        if key and not key.startswith("whsec_"):
            raise forms.ValidationError("El webhook secret debe comenzar con whsec_.")
        if not key and self.instance and self.instance.pk:
            return self.instance.webhook_secret
        return key


class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = [
            "key",
            "name",
            "description",
            "features",
            "unit_amount",
            "currency",
            "billing_interval",
            "stripe_price_id",
            "is_free",
            "is_active",
            "order",
        ]
        labels = {
            "key": "Clave interna",
            "name": "Nombre",
            "description": "Descripcion",
            "features": "Caracteristicas",
            "unit_amount": "Precio",
            "currency": "Moneda",
            "billing_interval": "Intervalo",
            "stripe_price_id": "Stripe Price ID",
            "is_free": "Plan gratis",
            "is_active": "Plan activo",
            "order": "Orden",
        }
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control", "placeholder": "starter, business, premium"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del plan"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripcion corta del plan"}),
            "features": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Una caracteristica por linea"}),
            "unit_amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"class": "form-control", "maxlength": "3", "placeholder": "USD"}),
            "billing_interval": forms.Select(attrs={"class": "form-control"}),
            "stripe_price_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "price_..."}),
            "is_free": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }
        help_texts = {
            "key": "No la cambies si ya hay suscripciones usando este plan.",
            "stripe_price_id": "Necesario para planes pagos por Stripe Checkout.",
        }

    def clean_key(self):
        return (self.cleaned_data["key"] or "").strip().lower()

    def clean_currency(self):
        return (self.cleaned_data["currency"] or "USD").strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get("is_free")
        unit_amount = cleaned_data.get("unit_amount")
        stripe_price_id = (cleaned_data.get("stripe_price_id") or "").strip()
        if is_free and unit_amount and unit_amount > 0:
            self.add_error("unit_amount", "Un plan gratis debe tener precio 0.")
        if not is_free and unit_amount == 0:
            self.add_error("unit_amount", "Un plan pago debe tener precio mayor que 0.")
        if not is_free and not stripe_price_id:
            self.add_error("stripe_price_id", "Agrega el Price ID de Stripe para planes pagos.")
        return cleaned_data


def normalize_whatsapp_url(value):
    raw_value = (value or "").strip()
    if not raw_value:
        return raw_value

    phone_candidate = re.sub(r"[\s().-]", "", raw_value)
    if re.fullmatch(r"\+?\d{7,15}", phone_candidate):
        return f"https://wa.me/{phone_candidate.lstrip('+')}"

    candidate = raw_value if "://" in raw_value else f"https://{raw_value}"
    parsed = urlparse(candidate)
    host = parsed.netloc.lower()

    if host not in WHATSAPP_ALLOWED_HOSTS:
        raise forms.ValidationError("Ingresa un enlace valido de WhatsApp, por ejemplo https://wa.me/18095550100.")

    if host in {"wa.me", "www.wa.me"}:
        number = parsed.path.strip("/")
        if not re.fullmatch(r"\+?\d{7,15}", number):
            raise forms.ValidationError("El enlace de WhatsApp debe incluir un numero valido.")
        return f"https://wa.me/{number.lstrip('+')}"

    query_phone = parse_qs(parsed.query).get("phone", [""])[0]
    if query_phone:
        normalized_phone = re.sub(r"[\s().+-]", "", query_phone)
        if re.fullmatch(r"\d{7,15}", normalized_phone):
            return f"https://wa.me/{normalized_phone}"

    return candidate


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "logo",
            "address",
            "phone_number",
            "email",
            "website",
            "description",
            "category",
            "services",
            "city",
            "region",
            "show_phone",
            "show_whatsapp",
            "show_email",
            "show_website",
            "show_address",
            "enable_quote_requests",
            "enable_appointments",
            "enable_messages",
            "enable_directions",
        ]
        labels = {
            "show_phone": "Mostrar boton de llamada",
            "show_whatsapp": "Mostrar WhatsApp",
            "show_email": "Mostrar email",
            "show_website": "Mostrar sitio web",
            "show_address": "Mostrar direccion",
            "enable_quote_requests": "Permitir solicitudes de cotizacion",
            "enable_appointments": "Permitir reservas o citas",
            "enable_messages": "Permitir mensajes",
            "enable_directions": "Permitir obtener direccion",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la empresa"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Direccion"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "empresa@email.com"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://empresa.com"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Descripcion breve"}),
            "category": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tecnologia, salud, servicios..."}),
            "services": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Servicios principales separados por coma"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ciudad"}),
            "region": forms.TextInput(attrs={"class": "form-control", "placeholder": "Region o estado"}),
            "show_phone": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_whatsapp": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_email": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_website": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_address": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "enable_quote_requests": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "enable_appointments": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "enable_messages": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "enable_directions": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BusinessPostForm(forms.ModelForm):
    class Meta:
        model = BusinessPost
        fields = ["company", "title", "caption", "media", "media_type"]
        widgets = {
            "company": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={
                "class": "form-control post-title-input",
                "placeholder": "Nueva actualizacion, servicio o logro",
                "maxlength": "100",
                "data-max-length": "100",
            }),
            "caption": forms.Textarea(attrs={
                "class": "form-control post-description-input",
                "rows": 7,
                "placeholder": "Escribe aqui la novedad de tu empresa...",
                "maxlength": "200",
                "data-max-length": "200",
            }),
            "media": forms.ClearableFileInput(attrs={
                "class": "form-control post-file-input",
                "data-post-file": "true",
                "accept": "image/png,image/jpeg,image/jpg",
            }),
            "media_type": forms.Select(attrs={"class": "form-control post-type-select", "data-post-type": "true"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = (
            Company.objects.filter(is_active=True, owner=self.user)
            | Company.objects.filter(is_active=True, members__user=self.user, members__is_active=True)
        ).distinct()

    def clean_company(self):
        company = self.cleaned_data["company"]
        if not can_access_company(self.user, company) and not user_has_access_permission(
            self.user,
            PERM_CREATE_CARDBOOK_BUSINESS_CARDS,
            company,
        ):
            raise forms.ValidationError("No perteneces a esta empresa.")
        return company

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if len(title) > 100:
            raise forms.ValidationError("El titulo no puede superar 100 caracteres.")
        return title

    def clean_caption(self):
        caption = (self.cleaned_data.get("caption") or "").strip()
        if len(caption) > 200:
            raise forms.ValidationError("La descripcion no puede superar 200 caracteres.")
        return caption

    def clean_media(self):
        media = self.cleaned_data.get("media")
        media_type = self.data.get(self.add_prefix("media_type")) or self.data.get("media_type")
        if not media:
            raise forms.ValidationError("Selecciona un archivo para la publicacion.")
        max_size = 50 * 1024 * 1024 if media_type == BusinessPost.MEDIA_VIDEO else 10 * 1024 * 1024
        if media.size > max_size:
            limit = "50MB" if media_type == BusinessPost.MEDIA_VIDEO else "10MB"
            raise forms.ValidationError(f"El archivo no puede superar {limit}.")
        content_type = getattr(media, "content_type", "")
        if media_type == BusinessPost.MEDIA_VIDEO and not content_type.startswith("video/"):
            raise forms.ValidationError("Para publicaciones de video debes subir un archivo de video.")
        if media_type == BusinessPost.MEDIA_IMAGE and not content_type.startswith("image/"):
            raise forms.ValidationError("Para publicaciones de imagen debes subir un archivo de imagen.")
        return media


class DigitalCardForm(forms.ModelForm):
    whatsapp_url = forms.CharField(
        required=False,
        label="WhatsApp",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://wa.me/18095550100 o solo el numero",
                "inputmode": "url",
            }
        ),
    )

    class Meta:
        model = DigitalCard
        fields = [
            "company",
            "job_title",
            "phone_number",
            "email",
            "website",
            "photo",
            "name_font",
            "name_size",
            "qr_shape",
            "qr_dot_color",
            "qr_marker_color",
            "qr_background_color",
            "whatsapp_url",
            "instagram_url",
            "facebook_url",
            "linkedin_url",
            "x_url",
            "youtube_url",
            "tiktok_url",
            "github_url",
            "infaithcore_url",
        ]
        labels = {
            "qr_shape": "Estilo del QR",
            "name_font": "Tipografia del nombre",
            "name_size": "Tamano del nombre",
            "qr_dot_color": "Color de puntos",
            "qr_marker_color": "Color de marcadores",
            "qr_background_color": "Color de fondo",
            "whatsapp_url": "WhatsApp",
            "instagram_url": "Instagram",
            "facebook_url": "Facebook",
            "linkedin_url": "LinkedIn",
            "x_url": "X / Twitter",
            "youtube_url": "YouTube",
            "tiktok_url": "TikTok",
            "github_url": "GitHub",
            "infaithcore_url": "Infaithcore",
        }
        widgets = {
            "company": forms.Select(attrs={"class": "form-control"}),
            "job_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cargo o posicion"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "persona@email.com"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "name_font": forms.Select(attrs={"class": "form-control"}),
            "name_size": forms.Select(attrs={"class": "form-control"}),
            "qr_shape": forms.Select(attrs={"class": "form-control"}),
            "qr_dot_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "qr_marker_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "qr_background_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "instagram_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://instagram.com/usuario"}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://facebook.com/usuario"}),
            "linkedin_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://linkedin.com/in/usuario"}),
            "x_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://x.com/usuario"}),
            "youtube_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://youtube.com/@usuario"}),
            "tiktok_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://tiktok.com/@usuario"}),
            "github_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://github.com/usuario"}),
            "infaithcore_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://infaithcore.com/usuario"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = profile_creation_companies(self.user)

    def clean_company(self):
        company = self.cleaned_data["company"]
        if not can_create_profile_for_company(self.user, company):
            raise forms.ValidationError("No perteneces a esta empresa.")
        return company

    def clean_whatsapp_url(self):
        return normalize_whatsapp_url(self.cleaned_data.get("whatsapp_url"))


class BusinessCardForm(forms.ModelForm):
    class Meta:
        model = BusinessCard
        fields = [
            "profile",
            "display_name",
            "job_title",
            "company_name",
            "name_font",
            "name_size",
            "phone_number",
            "email",
            "website",
            "address",
            "tagline",
            "services",
            "orientation",
            "accent_color",
            "background_color",
            "text_color",
            "show_profile_photo",
            "include_qr",
            "hide_direct_contact_on_print",
            "contact_cta_label",
            "contact_cta_color",
            "contact_cta_text_color",
        ]
        labels = {
            "profile": "Perfil del negocio",
            "display_name": "Nombre",
            "job_title": "Cargo",
            "company_name": "Empresa",
            "name_font": "Tipografia del nombre",
            "name_size": "Tamano del nombre",
            "phone_number": "Telefono",
            "email": "Email",
            "website": "Website",
            "address": "Direccion",
            "tagline": "Frase corta",
            "services": "Servicios",
            "orientation": "Orientacion",
            "accent_color": "Color de acento",
            "background_color": "Color de fondo",
            "text_color": "Color de texto",
            "show_profile_photo": "Mostrar foto de perfil",
            "include_qr": "Incluir QR al perfil",
            "hide_direct_contact_on_print": "Ocultar contacto directo en impresion",
            "contact_cta_label": "Texto del boton de contacto",
            "contact_cta_color": "Color del boton de contacto",
            "contact_cta_text_color": "Color del texto del boton",
        }
        widgets = {
            "profile": forms.Select(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo"}),
            "job_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cargo o posicion"}),
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la empresa"}),
            "name_font": forms.Select(attrs={"class": "form-control"}),
            "name_size": forms.Select(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "persona@email.com"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://empresa.com"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Direccion comercial"}),
            "tagline": forms.TextInput(attrs={"class": "form-control", "placeholder": "Soluciones digitales para empresas modernas"}),
            "services": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Consultoria, desarrollo web, soporte tecnico..."}),
            "orientation": forms.Select(attrs={"class": "form-control"}),
            "accent_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "background_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "text_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "show_profile_photo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "include_qr": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hide_direct_contact_on_print": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "contact_cta_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Contactanos"}),
            "contact_cta_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
            "contact_cta_text_color": forms.TextInput(attrs={"class": "form-control color-input", "type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        profiles = usable_profiles_for_business_cards(self.user)
        self.fields["profile"].queryset = profiles
        self.fields["profile"].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username} - {obj.company.name}"

        if not self.instance.pk:
            profile = profiles.first()
            if profile:
                self.fields["display_name"].initial = profile.user.get_full_name() or profile.user.username
                self.fields["job_title"].initial = profile.job_title
                self.fields["company_name"].initial = profile.company.name
                self.fields["phone_number"].initial = profile.phone_number
                self.fields["email"].initial = profile.email
                self.fields["website"].initial = profile.website

    def clean_profile(self):
        profile = self.cleaned_data["profile"]
        if not can_use_profile_for_business_card(self.user, profile):
            raise forms.ValidationError("No tienes permiso para usar este perfil.")
        return profile
