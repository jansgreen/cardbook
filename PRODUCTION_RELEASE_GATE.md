# Production Release Gate

Fase 8 agrega una puerta unica de validacion antes de publicar Cardbook.

## Objetivo

Evitar deploys incompletos o builds moviles con fallos silenciosos. Esta fase conecta los checks principales del backend, los modulos criticos y Flutter en un flujo repetible.

## Comando local recomendado

Desde la raiz del proyecto activo:

```powershell
.\tool\production_gate.ps1
```

Modo rapido sin Flutter, staticfiles ni smoke remoto:

```powershell
.\tool\production_gate.ps1 -SkipFlutter -SkipCollectstatic -SkipSmoke
```

## Que valida

- `manage.py check`.
- Migraciones pendientes con `makemigrations --dry-run --check`.
- Tests criticos:
  - `mobile`
  - `accesscontrol`
  - `ai_agents`
  - `financial_analytics`
  - `forms_builder`
  - `websitebuilder`
  - `web.tests_mvp_flow`
- `collectstatic`.
- Flutter:
  - `flutter pub get`
  - `flutter analyze`
  - `flutter test`
- Smoke remoto contra Heroku cuando no se omite.

## CI

GitHub Actions ahora ejecuta:

- Check de Django.
- Check de migraciones pendientes.
- Tests criticos del producto.
- `collectstatic`.
- Analisis y tests de Flutter.

## Deploy correcto

La rama activa de trabajo es `stable/cardbook-core`. Para desplegar a Heroku:

```powershell
git push heroku stable/cardbook-core:main
heroku run python manage.py migrate --app cardbook
heroku open --app cardbook
```

No usar `git push heroku master`.

## Criterio de cierre

La fase queda lista cuando:

- El comando rapido pasa localmente.
- CI queda preparado para bloquear regresiones principales.
- El flujo de deploy documenta la rama correcta.
