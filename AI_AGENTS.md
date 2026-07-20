# Cardbook AI Agents

Modulo de asistentes IA sin costo basado en reglas, FAQ y base de conocimiento de cada empresa.

## Endpoints REST

Todos los endpoints privados usan JWT Bearer y viven bajo:

`/api/v1/ai-agents/`

Rutas principales:

- `GET /api/v1/ai-agents/` lista agentes disponibles para el usuario.
- `GET /api/v1/ai-agents/{id}/` detalle del agente.
- `PATCH /api/v1/ai-agents/{id}/` edita configuracion permitida.
- `GET /api/v1/ai-agents/{id}/analytics/` metricas del agente.
- `POST /api/v1/ai-agents/{id}/test/` prueba una pregunta sin guardar conversacion real.
- `GET/POST /api/v1/ai-agents/{id}/knowledge/` lista o crea conocimiento.
- `PATCH/DELETE /api/v1/ai-agents/{id}/knowledge/{item_id}/` actualiza o elimina conocimiento.
- `GET/POST /api/v1/ai-agents/{id}/faqs/` lista o crea FAQ.
- `PATCH/DELETE /api/v1/ai-agents/{id}/faqs/{faq_id}/` actualiza o elimina FAQ.
- `GET /api/v1/ai-agents/{id}/leads/` lista leads capturados.
- `PATCH /api/v1/ai-agents/{id}/leads/{lead_id}/` actualiza estado de lead.
- `GET/POST /api/v1/ai-agents/{id}/training-gaps/` consulta preguntas sin respuesta o crea FAQ desde una brecha.
- `POST /api/v1/ai-agents/{id}/sync-knowledge/` sincroniza conocimiento desde empresa/website.

El widget publico usa:

`POST /ai/public/ask/`

## Variables de entorno

Limites recomendados para produccion:

```env
AI_AGENT_PUBLIC_ASK_LIMIT=30
AI_AGENT_PUBLIC_ASK_WINDOW_SECONDS=60
AI_AGENT_PUBLIC_LEAD_LIMIT=5
AI_AGENT_PUBLIC_LEAD_WINDOW_SECONDS=3600
AI_AGENT_MAX_QUESTION_LENGTH=500
AI_AGENT_MAX_LEAD_FIELD_LENGTH=255
AI_AGENT_MAX_LEAD_MESSAGE_LENGTH=1200
```

## Seguridad incluida

- Rate limit para preguntas publicas.
- Rate limit para leads publicos.
- Campo honeypot contra bots simples.
- Validacion de email.
- Validacion basica de telefono.
- Recorte de longitud de preguntas y campos.
- Permisos por empresa para endpoints privados.

## Checklist antes de deploy

1. Confirmar que `DJANGO_DEBUG=False`.
2. Configurar `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS`.
3. Definir variables `AI_AGENT_*` segun trafico esperado.
4. Ejecutar `python manage.py migrate`.
5. Ejecutar `python manage.py check`.
6. Ejecutar `python manage.py test ai_agents`.
7. Verificar que `/api/v1/mobile/config/` incluya `ai_agents.list`.
8. Probar un website publico con widget activo.
9. Probar entrenamiento desde `training-gaps`.

