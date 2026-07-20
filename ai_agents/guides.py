DEFAULT_GUIDE_STEPS = [
    {
        "title": "Navegacion principal",
        "body": "Usa este menu para moverte entre empresas, tarjetas, Book, agentes, estadisticas y configuracion.",
        "selector": ".dashboard-sidebar",
    },
    {
        "title": "Area de trabajo",
        "body": "Aqui aparece la herramienta activa. Cada modulo conserva el mismo estilo para que no tengas que reaprender la plataforma.",
        "selector": ".dashboard-main",
    },
]


GUIDE_LIBRARY = {
    "dashboard-home": {
        "title": "Guia rapida del resumen",
        "intro": "Este panel te muestra el estado general de tu presencia digital en Cardbook.",
        "steps": [
            {
                "title": "Metricas principales",
                "body": "Estas tarjetas resumen empresas, perfiles, presentaciones y vistas.",
                "selector": ".stats-grid",
            },
            {
                "title": "Asistente de negocio",
                "body": "El asistente revisa tu empresa y recomienda el proximo paso mas importante.",
                "selector": ".ai-business-card",
            },
            {
                "title": "Accesos rapidos",
                "body": "Desde aqui puedes crear empresas, perfiles, tarjetas o abrir el agente IA.",
                "selector": ".quick-actions",
            },
        ],
    },
    "dashboard-companies": {
        "title": "Guia del centro empresarial",
        "intro": "Esta pantalla concentra la gestion de empresa, publicaciones, alianzas y actividad.",
        "steps": [
            {
                "title": "Empresa activa",
                "body": "Selecciona la empresa que quieres administrar y revisa su informacion publica.",
                "selector": ".business-hero-card",
            },
            {
                "title": "Publicaciones",
                "body": "Crea novedades, proyectos y logros para mantener activa tu red empresarial.",
                "selector": ".post-create-module",
            },
            {
                "title": "Asistente compacto",
                "body": "El asistente te acompana con una recomendacion concreta sin salir del panel.",
                "selector": ".ai-business-card",
            },
            {
                "title": "Empresas sugeridas",
                "body": "Usa esta zona para detectar alianzas y negocios afines.",
                "selector": "#sugeridas",
            },
        ],
    },
    "dashboard-ai-agents": {
        "title": "Guia de agentes IA",
        "intro": "Aqui configuras y revisas los asistentes sin costo de tus empresas.",
        "steps": [
            {
                "title": "Estado general",
                "body": "Estas metricas resumen agentes, empresas y sugerencias activas.",
                "selector": ".ai-agent-stats",
            },
            {
                "title": "Lista de agentes",
                "body": "Cada empresa puede tener un asistente interno y un asistente publico para su website.",
                "selector": ".ai-agent-list",
            },
            {
                "title": "Recomendaciones",
                "body": "El motor basado en reglas detecta datos faltantes y acciones pendientes.",
                "selector": ".ai-agent-suggestions",
            },
            {
                "title": "Configuracion",
                "body": "Controla tono, estado y visibilidad sin conectar aun una API paga.",
                "selector": ".ai-agent-config",
            },
        ],
    },
    "dashboard-cards": {
        "title": "Guia de perfiles del negocio",
        "intro": "Los perfiles digitales son la base para compartir tu empresa con QR y enlaces.",
        "steps": DEFAULT_GUIDE_STEPS,
    },
    "dashboard-business-cards": {
        "title": "Guia de tarjetas de presentacion",
        "intro": "Las tarjetas ayudan a empleados y equipos a compartir contactos profesionales.",
        "steps": DEFAULT_GUIDE_STEPS,
    },
    "dashboard-book": {
        "title": "Guia de Book",
        "intro": "Book guarda empresas, tarjetas y perfiles que otros negocios comparten contigo.",
        "steps": DEFAULT_GUIDE_STEPS,
    },
    "dashboard-white-card-job": {
        "title": "Guia de White Card Job",
        "intro": "Aqui puedes crear y administrar tarjetas blancas para buscar oportunidades laborales.",
        "steps": DEFAULT_GUIDE_STEPS,
    },
}


def get_dashboard_guide_payload(request):
    if not request.user.is_authenticated:
        return {"enabled": False}
    if not request.path.startswith("/dashboard/"):
        return {"enabled": False}

    url_name = request.resolver_match.url_name if request.resolver_match else ""
    guide = GUIDE_LIBRARY.get(url_name, {
        "title": "Guia Cardbook",
        "intro": "Te acompano con pasos cortos para entender esta pantalla.",
        "steps": DEFAULT_GUIDE_STEPS,
    })

    steps = guide["steps"]
    return {
        "enabled": True,
        "route": url_name or "dashboard",
        "title": guide["title"],
        "intro": guide["intro"],
        "steps": steps,
        "total": len(steps),
    }
