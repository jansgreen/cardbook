from django import forms

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


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "logo", "address", "phone_number", "email", "website", "description", "category", "services", "city", "region"]
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
            "whatsapp_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://wa.me/18095550100"}),
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
            "include_qr",
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
            "include_qr": "Incluir QR al perfil",
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
            "include_qr": forms.CheckboxInput(attrs={"class": "form-check-input"}),
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
