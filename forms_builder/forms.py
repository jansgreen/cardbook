from django import forms

from .models import FormDefinition, FormField


class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = ["name", "slug", "description", "recipient_email", "success_message", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Contacto, Cotizacion, Solicitud de servicio..."}),
            "slug": forms.TextInput(attrs={"placeholder": "contacto"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Explica para que se usa este formulario."}),
            "recipient_email": forms.EmailInput(attrs={"placeholder": "ventas@empresa.com"}),
            "success_message": forms.TextInput(attrs={"placeholder": "Mensaje mostrado despues de enviar."}),
        }

    def __init__(self, *args, company=None, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)

    def clean_slug(self):
        return (self.cleaned_data.get("slug") or "").strip().lower()

    def clean(self):
        cleaned = super().clean()
        slug = cleaned.get("slug")
        if slug and self.company:
            queryset = FormDefinition.objects.filter(company=self.company, slug=slug)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error("slug", "Ya existe un formulario con este slug para esta empresa.")
        return cleaned


class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = [
            "label",
            "field_type",
            "placeholder",
            "help_text",
            "choices",
            "is_required",
            "order",
            "is_active",
        ]
        widgets = {
            "label": forms.TextInput(attrs={"placeholder": "Nombre, Email, Servicio..."}),
            "placeholder": forms.TextInput(attrs={"placeholder": "Texto de ayuda dentro del campo"}),
            "help_text": forms.TextInput(attrs={"placeholder": "Nota corta visible bajo el campo"}),
            "choices": forms.Textarea(attrs={"rows": 4, "placeholder": "Opcion 1\nOpcion 2\nOpcion 3"}),
            "order": forms.NumberInput(attrs={"min": "0"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("field_type") == FormField.SELECT and not cleaned.get("choices"):
            self.add_error("choices", "Agrega al menos una opcion para el selector.")
        return cleaned


class PublicFormSubmissionForm(forms.Form):
    def __init__(self, form_definition, *args, **kwargs):
        self.form_definition = form_definition
        super().__init__(*args, **kwargs)
        for field in form_definition.fields.filter(is_active=True):
            field_name = f"field_{field.id}"
            attrs = {"placeholder": field.placeholder}
            common = {"label": field.label, "required": field.is_required, "help_text": field.help_text}
            if field.field_type == FormField.TEXTAREA:
                self.fields[field_name] = forms.CharField(widget=forms.Textarea(attrs={**attrs, "rows": 4}), **common)
            elif field.field_type == FormField.EMAIL:
                self.fields[field_name] = forms.EmailField(widget=forms.EmailInput(attrs=attrs), **common)
            elif field.field_type == FormField.PHONE:
                self.fields[field_name] = forms.CharField(widget=forms.TextInput(attrs={**attrs, "inputmode": "tel"}), **common)
            elif field.field_type == FormField.SELECT:
                choices = [("", "Selecciona una opcion")] + [(choice, choice) for choice in field.choice_list()]
                self.fields[field_name] = forms.ChoiceField(choices=choices, widget=forms.Select(attrs=attrs), **common)
            elif field.field_type == FormField.CHECKBOX:
                self.fields[field_name] = forms.BooleanField(required=field.is_required, label=field.label, help_text=field.help_text)
            elif field.field_type == FormField.NUMBER:
                self.fields[field_name] = forms.DecimalField(widget=forms.NumberInput(attrs=attrs), **common)
            elif field.field_type == FormField.DATE:
                self.fields[field_name] = forms.DateField(widget=forms.DateInput(attrs={**attrs, "type": "date"}), **common)
            else:
                self.fields[field_name] = forms.CharField(widget=forms.TextInput(attrs=attrs), **common)

    def cleaned_submission_data(self):
        data = {}
        sender_email = ""
        sender_name = ""
        active_fields = {f"field_{field.id}": field for field in self.form_definition.fields.filter(is_active=True)}
        for field_name, value in self.cleaned_data.items():
            field = active_fields.get(field_name)
            if not field:
                continue
            normalized = str(value) if value is not None else ""
            data[field.label] = normalized
            label = field.label.lower()
            if not sender_email and field.field_type == FormField.EMAIL:
                sender_email = normalized
            if not sender_name and ("nombre" in label or "name" in label):
                sender_name = normalized
        return data, sender_name, sender_email

