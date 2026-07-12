from django import forms

from .models import CompanySpecialty, Specialty, WhiteCardJob
from .services import user_has_company


class WhiteCardJobForm(forms.ModelForm):
    category = forms.ChoiceField(
        required=True,
        label="Categoria de trabajo",
        widget=forms.Select(attrs={"class": "form-control", "data-job-category": "true"}),
    )

    class Meta:
        model = WhiteCardJob
        fields = [
            "title",
            "photo",
            "phone_number",
            "address",
            "linkedin_url",
            "resume_url",
            "specialty",
            "short_description",
            "languages",
            "technologies",
            "certifications",
            "is_available",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Busco Trabajo"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 809 555 0100"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ciudad, Estado"}),
            "linkedin_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://linkedin.com/in/usuario"}),
            "resume_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://drive.google.com/..."}),
            "specialty": forms.Select(attrs={"class": "form-control", "data-job-specialty": "true"}),
            "short_description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "maxlength": 420}),
            "languages": forms.TextInput(attrs={"class": "form-control", "placeholder": "Espanol nativo, Ingles basico"}),
            "technologies": forms.TextInput(attrs={"class": "form-control", "placeholder": "Herramientas, software o tecnologias"}),
            "certifications": forms.TextInput(attrs={"class": "form-control", "placeholder": "Certificaciones relevantes"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        categories = list(
            Specialty.objects.exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        self.fields["category"].choices = [("", "Selecciona una categoria")] + [(category, category) for category in categories]

        selected_category = self.data.get(self.add_prefix("category")) or self.initial.get("category")
        if self.instance.pk and self.instance.specialty_id:
            selected_category = selected_category or self.instance.specialty.category
            self.fields["category"].initial = selected_category

        specialty_queryset = Specialty.objects.all()
        if selected_category:
            specialty_queryset = specialty_queryset.filter(category=selected_category)
        self.fields["specialty"].queryset = specialty_queryset

        if not selected_category:
            self.fields["specialty"].help_text = "Primero selecciona la categoria para ver los trabajos disponibles."

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and user_has_company(self.user):
            raise forms.ValidationError("Solo los usuarios sin empresa pueden crear una White Card Job.")
        category = cleaned.get("category")
        specialty = cleaned.get("specialty")
        if specialty and category and specialty.category != category:
            raise forms.ValidationError("La especialidad seleccionada no pertenece a la categoria elegida.")
        return cleaned


class CompanySpecialtyForm(forms.Form):
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Especialidades de la empresa",
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["specialties"].initial = CompanySpecialty.objects.filter(company=company).values_list("specialty_id", flat=True)
