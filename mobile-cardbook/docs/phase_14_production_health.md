# Fase 14 - Health checks y hardening base

Esta fase agrega endpoints de salud para diagnosticar despliegues y refuerza configuracion de produccion sin romper desarrollo local.

## Endpoints

```text
GET /health/
GET /health/ready/
```

`/health/` confirma que Django esta respondiendo.

`/health/ready/` tambien valida conexion a base de datos y responde `503` si la base de datos no esta lista.

## Variables nuevas

```text
CARDBOOK_APP_VERSION=0.14.0
CARDBOOK_DEPLOY_ENV=production
CARDBOOK_RELEASE_COMMIT=local
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.com
DJANGO_SECURE_SSL_REDIRECT=True
```

En Heroku, `HEROKU_SLUG_COMMIT` se usa automaticamente como commit cuando existe.

## Produccion

Para Heroku:

```powershell
heroku config:set CARDBOOK_APP_VERSION=0.14.0 --app cardbook
heroku config:set CARDBOOK_DEPLOY_ENV=production --app cardbook
heroku config:set DJANGO_DEBUG=False --app cardbook
heroku config:set DJANGO_SECURE_SSL_REDIRECT=True --app cardbook
heroku config:set DJANGO_CSRF_TRUSTED_ORIGINS=https://incardbook.com --app cardbook
```

## Auditoria

La auditoria de release ahora consulta:

- `/health/`
- `/health/ready/`
- `/privacy/`
- `/terms/`
- `/android/version/`

