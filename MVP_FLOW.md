# Cardbook MVP Flow

Este documento define el flujo minimo que debe funcionar antes de una beta privada.

## Flujo principal

1. Usuario se registra.
2. Usuario inicia sesion y recibe JWT.
3. Usuario crea una empresa.
4. Sistema crea membresia owner para esa empresa.
5. Usuario crea un perfil de negocio.
6. Usuario crea una tarjeta de presentacion usando ese perfil.
7. Usuario crea/publica website empresarial.
8. Website publico renderiza correctamente.
9. Agente IA publico responde desde el website.
10. Agente IA captura un lead.
11. Otro usuario guarda la tarjeta/empresa en Book.
12. App movil puede descubrir endpoints desde `/api/v1/mobile/config/`.

## Endpoints criticos

```http
POST /api/v1/accounts/register/
POST /api/v1/accounts/login/
GET /api/v1/mobile/config/
POST /api/v1/companies/
POST /api/v1/cards/
POST /api/v1/cards/business-cards/
GET /site/{website_slug}/
POST /ai/public/ask/
POST /api/v1/book/
```

## Prueba automatizada

La cobertura integrada vive en:

`web/tests_mvp_flow.py`

Comando:

```bash
cb_env\Scripts\python.exe manage.py test web.tests_mvp_flow
```

## Criterio de aceptacion

La fase MVP se considera sana cuando:

- El test integrado pasa.
- `manage.py check` no reporta errores.
- No hay migraciones pendientes.
- Las URLs publicas de tarjeta, business card y website se generan.
- El Book rechaza guardar empresas propias y permite guardar empresas externas.

