from django import forms

from .models import Block, Component, Page, Section


SERVICE_ICON_CHOICES = [
    ("briefcase", "Negocio"),
    ("wrench", "Herramienta"),
    ("scissors", "Costura / corte"),
    ("car", "Automotriz"),
    ("laptop", "Tecnologia"),
    ("brush", "Pintura / diseno"),
    ("home", "Hogar"),
    ("heart", "Salud / cuidado"),
    ("shield", "Seguridad"),
    ("package", "Producto"),
    ("phone", "Contacto"),
    ("star", "Destacado"),
]


class PageDashboardForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = [
            "title",
            "slug",
            "icon",
            "order",
            "is_homepage",
            "is_published",
            "show_in_menu",
            "seo_title",
            "seo_description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Inicio, Servicios, Contacto..."}),
            "slug": forms.TextInput(attrs={"placeholder": "servicios"}),
            "icon": forms.TextInput(attrs={"placeholder": "home, briefcase, mail..."}),
            "order": forms.NumberInput(attrs={"min": "0"}),
            "seo_title": forms.TextInput(attrs={"placeholder": "Titulo para buscadores"}),
            "seo_description": forms.Textarea(attrs={"rows": 3, "placeholder": "Descripcion corta para SEO"}),
        }

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        return slug


class SectionDashboardForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = [
            "section_type",
            "html_tag",
            "name",
            "title",
            "subtitle",
            "background_color",
            "order",
            "is_active",
        ]
        widgets = {
            "section_type": forms.Select(),
            "html_tag": forms.Select(),
            "name": forms.TextInput(attrs={"placeholder": "Hero principal, Servicios, CTA..."}),
            "title": forms.TextInput(attrs={"placeholder": "Titulo visible de la seccion"}),
            "subtitle": forms.Textarea(attrs={"rows": 3, "placeholder": "Texto de apoyo o descripcion"}),
            "background_color": forms.TextInput(attrs={"type": "color"}),
            "order": forms.NumberInput(attrs={"min": "0"}),
        }


class ComponentDashboardForm(forms.ModelForm):
    service_icon = forms.ChoiceField(
        choices=SERVICE_ICON_CHOICES,
        required=False,
        label="Icono",
    )

    class Meta:
        model = Component
        fields = [
            "component_type",
            "name",
            "title",
            "subtitle",
            "order",
            "is_active",
        ]
        widgets = {
            "component_type": forms.Select(),
            "name": forms.TextInput(attrs={"placeholder": "Tarjeta de servicio, Botones hero..."}),
            "title": forms.TextInput(attrs={"placeholder": "Titulo del componente"}),
            "subtitle": forms.Textarea(attrs={"rows": 2, "placeholder": "Texto secundario"}),
            "order": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["service_icon"].initial = (self.instance.settings or {}).get("icon", "briefcase")

    def save(self, commit=True):
        component = super().save(commit=False)
        settings = dict(component.settings or {})
        settings["icon"] = self.cleaned_data.get("service_icon") or "briefcase"
        component.settings = settings
        if commit:
            component.save()
            self.save_m2m()
        return component


class BlockDashboardForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = [
            "block_type",
            "key",
            "value",
            "text",
            "image",
            "video",
            "icon",
            "url",
            "button_text",
            "order",
            "is_active",
        ]
        widgets = {
            "block_type": forms.Select(),
            "key": forms.TextInput(attrs={"placeholder": "description, primary, phone..."}),
            "value": forms.TextInput(attrs={"placeholder": "Valor corto"}),
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Texto largo"}),
            "image": forms.ClearableFileInput(),
            "video": forms.ClearableFileInput(),
            "icon": forms.TextInput(attrs={"placeholder": "star, phone, mail..."}),
            "url": forms.URLInput(attrs={"placeholder": "https://..."}),
            "button_text": forms.TextInput(attrs={"placeholder": "Contactar, Ver mas..."}),
            "order": forms.NumberInput(attrs={"min": "0"}),
        }
