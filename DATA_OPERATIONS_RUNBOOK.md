# Data Operations Runbook

Fase 10 agrega una foto operativa segura del estado de Cardbook.

## Snapshot operativo

Comando:

```powershell
.\cb_env\Scripts\python.exe manage.py ops_snapshot --json
```

El snapshot resume:

- Usuarios activos y staff.
- Empresas activas.
- Perfiles digitales.
- Tarjetas de presentacion.
- White Card Jobs.
- Websites publicados.
- Formularios y submissions.
- Agentes IA activos.
- Backend de media/static configurado.

No imprime emails, telefonos, passwords, tokens, API keys ni secretos.

## Uso antes de deploy

El gate de produccion ahora ejecuta `ops_snapshot --json` despues de los tests criticos:

```powershell
.\tool\production_gate.ps1 -SkipFlutter -SkipCollectstatic -SkipSmoke
```

## Uso despues de deploy

En Heroku:

```powershell
heroku run python manage.py ops_snapshot --json --app cardbook
```

Esto confirma que el dyno puede acceder a la base de datos y que los modelos principales cargan sin romper imports.

## Recomendacion de backups

Para base de datos Heroku Postgres:

```powershell
heroku pg:backups:capture --app cardbook
heroku pg:backups:download --app cardbook
```

Para media en S3, revisar lifecycle/versioning directamente en el bucket.

## Criterio de cierre

La fase queda lista cuando:

- `ops_snapshot --json` corre sin exponer datos sensibles.
- El gate de produccion ejecuta el snapshot.
- Existe runbook para backup manual.
