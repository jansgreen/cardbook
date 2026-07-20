from django import forms

from .models import AIAgent, AIAgentFAQ, AIAgentKnowledgeBase, AIAgentLead


class AIAgentSettingsForm(forms.ModelForm):
    class Meta:
        model = AIAgent
        fields = [
            "name",
            "status",
            "mode",
            "tone",
            "default_language",
            "welcome_message",
            "fallback_message",
            "can_capture_leads",
            "show_on_website",
        ]
        widgets = {
            "welcome_message": forms.Textarea(attrs={"rows": 3}),
            "fallback_message": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_mode(self):
        mode = self.cleaned_data["mode"]
        if mode != AIAgent.MODE_RULE_BASED:
            raise forms.ValidationError("Por ahora Cardbook solo tiene habilitado el modo sin costo basado en reglas.")
        return mode


class AIAgentKnowledgeBaseForm(forms.ModelForm):
    class Meta:
        model = AIAgentKnowledgeBase
        fields = ["category", "title", "content", "is_public", "is_active"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4, "placeholder": "Escribe datos claros que el agente pueda usar para responder."}),
        }


class AIAgentFAQForm(forms.ModelForm):
    class Meta:
        model = AIAgentFAQ
        fields = ["question", "answer", "keywords", "is_public", "is_active"]
        widgets = {
            "answer": forms.Textarea(attrs={"rows": 4, "placeholder": "Respuesta breve, concreta y lista para el cliente."}),
            "keywords": forms.TextInput(attrs={"placeholder": "servicio, precio, horario"}),
        }


class AIAgentLeadStatusForm(forms.ModelForm):
    class Meta:
        model = AIAgentLead
        fields = ["status", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "Nota interna sobre este lead."}),
        }
