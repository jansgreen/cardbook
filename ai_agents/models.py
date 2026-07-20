from django.conf import settings
from django.db import models

from companies.models import Company
from websitebuilder.models import Website


class AIAgent(models.Model):
    TYPE_BUSINESS_ASSISTANT = "business_assistant"
    TYPE_GUIDE = "guide"
    TYPE_WEBSITE_ASSISTANT = "website_assistant"

    AGENT_TYPE_CHOICES = [
        (TYPE_BUSINESS_ASSISTANT, "Asistente de negocio"),
        (TYPE_GUIDE, "Guia de plataforma"),
        (TYPE_WEBSITE_ASSISTANT, "Asistente publico del website"),
    ]

    MODE_RULE_BASED = "rule_based"
    MODE_HYBRID = "hybrid"
    MODE_LLM = "llm"

    MODE_CHOICES = [
        (MODE_RULE_BASED, "Reglas sin costo"),
        (MODE_HYBRID, "Hibrido"),
        (MODE_LLM, "IA conectada"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Borrador"),
        (STATUS_ACTIVE, "Activo"),
        (STATUS_PAUSED, "Pausado"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_agents", blank=True, null=True)
    website = models.ForeignKey(Website, on_delete=models.SET_NULL, related_name="ai_agents", blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="created_ai_agents", blank=True, null=True)
    name = models.CharField(max_length=140)
    agent_type = models.CharField(max_length=40, choices=AGENT_TYPE_CHOICES, default=TYPE_BUSINESS_ASSISTANT)
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default=MODE_RULE_BASED)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    default_language = models.CharField(max_length=8, default="es")
    tone = models.CharField(max_length=80, default="profesional y cercano")
    welcome_message = models.CharField(max_length=255, blank=True)
    fallback_message = models.CharField(
        max_length=255,
        default="Todavia no tengo esa respuesta. Puedo tomar tus datos para que la empresa te contacte.",
    )
    can_capture_leads = models.BooleanField(default=True)
    show_on_website = models.BooleanField(default=False)
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company__name", "agent_type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "agent_type"], name="unique_ai_agent_type_per_company"),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_agent_type_display()}"

    @property
    def is_rule_based(self):
        return self.mode == self.MODE_RULE_BASED


class AIAgentKnowledgeBase(models.Model):
    CATEGORY_GENERAL = "general"
    CATEGORY_SERVICES = "services"
    CATEGORY_HOURS = "hours"
    CATEGORY_PRICING = "pricing"
    CATEGORY_POLICY = "policy"

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, "General"),
        (CATEGORY_SERVICES, "Servicios"),
        (CATEGORY_HOURS, "Horarios"),
        (CATEGORY_PRICING, "Precios"),
        (CATEGORY_POLICY, "Politicas"),
    ]

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="knowledge_items")
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    title = models.CharField(max_length=160)
    content = models.TextField()
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return f"{self.agent} / {self.title}"


class AIAgentFAQ(models.Model):
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, help_text="Separar palabras clave por comas.")
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["question"]

    def __str__(self):
        return self.question


class AIAgentConversation(models.Model):
    CHANNEL_DASHBOARD = "dashboard"
    CHANNEL_WEBSITE = "website"
    CHANNEL_MOBILE = "mobile"

    CHANNEL_CHOICES = [
        (CHANNEL_DASHBOARD, "Dashboard"),
        (CHANNEL_WEBSITE, "Website publico"),
        (CHANNEL_MOBILE, "App movil"),
    ]

    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_LEAD = "lead"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Abierta"),
        (STATUS_CLOSED, "Cerrada"),
        (STATUS_LEAD, "Lead generado"),
    ]

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="conversations")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_conversations", blank=True, null=True)
    website = models.ForeignKey(Website, on_delete=models.SET_NULL, related_name="ai_conversations", blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="ai_conversations", blank=True, null=True)
    visitor_name = models.CharField(max_length=140, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=40, blank=True)
    session_key = models.CharField(max_length=120, blank=True)
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default=CHANNEL_DASHBOARD)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.agent} / {self.channel} / {self.created_at:%Y-%m-%d}"


class AIAgentMessage(models.Model):
    ROLE_USER = "user"
    ROLE_AGENT = "agent"
    ROLE_SYSTEM = "system"

    ROLE_CHOICES = [
        (ROLE_USER, "Usuario"),
        (ROLE_AGENT, "Agente"),
        (ROLE_SYSTEM, "Sistema"),
    ]

    conversation = models.ForeignKey(AIAgentConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    intent = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class AIAgentLead(models.Model):
    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_CLOSED = "closed"
    STATUS_CONVERTED = "converted"

    STATUS_CHOICES = [
        (STATUS_NEW, "Nuevo"),
        (STATUS_CONTACTED, "Contactado"),
        (STATUS_CLOSED, "Cerrado"),
        (STATUS_CONVERTED, "Convertido"),
    ]

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="leads")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_leads")
    conversation = models.ForeignKey(AIAgentConversation, on_delete=models.SET_NULL, related_name="leads", blank=True, null=True)
    name = models.CharField(max_length=140, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    service_interest = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or self.email or f"Lead #{self.pk}"


class AIAgentSuggestion(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Baja"),
        (PRIORITY_MEDIUM, "Media"),
        (PRIORITY_HIGH, "Alta"),
    ]

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="suggestions")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_suggestions")
    title = models.CharField(max_length=180)
    description = models.TextField()
    action_label = models.CharField(max_length=80, blank=True)
    action_url = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_resolved", "-priority", "-created_at"]

    def __str__(self):
        return self.title
