# Production Handoff

Fase 12 cierra el bloque de preparacion para una primera salida controlada de Cardbook.

## Estado cubierto

- API REST conservada para Android/Flutter.
- Capa web y dashboard validados por tests criticos.
- Website Builder y Forms Builder integrados.
- Finanzas con flujo web/API y refunds controlados.
- Agentes IA con dashboard, leads y exportacion CSV.
- Flutter nativo con diagnostico movil.
- Gate de produccion local.
- Observabilidad con `X-Request-ID`.
- Snapshot operativo seguro.
- QA visual del directorio publico.

## Comando dry run

Ejecuta validacion final sin desplegar:

```powershell
.\tool\release_heroku.ps1 -SkipFlutter -SkipCollectstatic -SkipSmokeBeforeDeploy
```

Validacion completa local:

```powershell
.\tool\release_heroku.ps1
```

## Deploy real

Cuando estes listo:

```powershell
.\tool\release_heroku.ps1 -Deploy
```

Este comando ejecuta:

- `production_gate`.
- `git push heroku stable/cardbook-core:main`.
- `heroku run --app cardbook --exit-code --no-tty -- python manage.py migrate`.
- `heroku run --app cardbook --exit-code --no-tty -- python manage.py ops_snapshot --json`.
- Smoke test publico.

## Deploy manual equivalente

```powershell
.\tool\production_gate.ps1
git push heroku stable/cardbook-core:main
heroku run --app cardbook --exit-code --no-tty -- python manage.py migrate
heroku run --app cardbook --exit-code --no-tty -- python manage.py ops_snapshot --json
.\mobile-cardbook\tool\smoke_heroku.ps1
```

## Config vars minimas de produccion

```powershell
heroku config:set DJANGO_DEBUG=False --app cardbook
heroku config:set CARDBOOK_DEPLOY_ENV=production --app cardbook
heroku config:set DJANGO_ALLOWED_HOSTS=incardbook.com,www.incardbook.com,cardbook-45cf0409dc07.herokuapp.com --app cardbook
heroku config:set DJANGO_CSRF_TRUSTED_ORIGINS=https://incardbook.com,https://www.incardbook.com,https://cardbook-45cf0409dc07.herokuapp.com --app cardbook
heroku config:set DJANGO_SECURE_SSL_REDIRECT=True --app cardbook
heroku config:set CARDBOOK_REQUEST_LOGGING_ENABLED=True --app cardbook
heroku config:set CARDBOOK_ENABLE_REQUEST_ID_HEADERS=True --app cardbook
```

Para produccion real tambien faltan valores privados:

- `DJANGO_SECRET_KEY`
- SMTP real
- S3/media persistente
- Stripe real
- Firebase FCM si se activan notificaciones moviles

## Smoke test post-deploy

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1
```

Si la app esta en beta y aun no tienes S3, SMTP o Stripe reales, puedes permitir `/health/ready/` degradado sin esconder las advertencias:

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1 -AllowReadinessWarnings
.\tool\release_heroku.ps1 -Deploy -AllowReadinessWarnings
```

Debe validar:

- `/health/`
- `/health/ready/`
- `/api/v1/`
- `/android/version/`
- `/`
- `/android/`
- `/privacy/`
- `/terms/`

## Rollback

Ver releases:

```powershell
heroku releases --app cardbook
```

Volver a una release anterior:

```powershell
heroku rollback vNUMERO --app cardbook
```

Despues del rollback:

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1
```

## Criterio de cierre

Fase 12 queda lista cuando:

- El dry run pasa localmente.
- Existe script unico de release.
- Existe documento de handoff.
- El deploy real queda reducido a un comando explicito y auditable.
