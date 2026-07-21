# Agentes IA

Fase 6 deja los agentes IA listos para operacion inicial sin depender de APIs pagas.

## Capacidades activas

- Agente interno de recomendaciones para mejorar empresas.
- Guia visual del dashboard para orientar al usuario.
- Agente publico por website empresarial.
- Base de conocimiento por empresa.
- FAQ entrenables desde preguntas sin respuesta.
- Widget publico con preguntas sugeridas.
- Captura de leads desde el website.
- Gestion de leads desde dashboard.
- Exportacion CSV de leads filtrados.
- Analytics basicos: conversaciones, preguntas, leads, conversion y preguntas frecuentes.

## Operacion comercial

Desde `/dashboard/ai-agents/` el usuario puede:

1. Sincronizar agentes con sus empresas.
2. Activar o pausar el agente.
3. Mostrarlo u ocultarlo en el website publico.
4. Sincronizar conocimiento desde empresa y website.
5. Agregar datos manuales y FAQ.
6. Probar respuestas antes de publicarlo.
7. Ver preguntas sin respuesta y convertirlas en FAQ.
8. Filtrar leads por estado o busqueda.
9. Exportar leads a CSV.

## Seguridad

- El dashboard requiere sesion autenticada.
- Los agentes solo son visibles para owners, miembros autorizados o usuarios con `ai_agents.manage`.
- El widget publico usa rate limit por pregunta y por lead.
- La captura de leads valida email, telefono y honeypot anti-spam.
- El modo LLM/Hibrido queda bloqueado hasta tener proveedor configurado; el modo actual es basado en reglas y sin costo.

## Garantia actual

La suite `ai_agents` cubre:

- Sincronizacion de agentes.
- Permisos de dashboard y API.
- Widget publico.
- Captura y gestion de leads.
- Exportacion CSV de leads.
- Rate limits y validaciones anti-spam.
- Analytics y entrenamiento desde preguntas sin respuesta.
