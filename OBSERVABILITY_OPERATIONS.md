# Observability Operations

Fase 9 agrega trazabilidad operativa para diagnosticar produccion con menos friccion.

## Request ID

Cada request recibe un `X-Request-ID`:

- Si el cliente envia `X-Request-ID`, Cardbook lo conserva.
- Si no existe, Cardbook genera uno.
- El valor se agrega al response cuando `CARDBOOK_ENABLE_REQUEST_ID_HEADERS=True`.

## Logging de requests

El middleware registra requests cuando:

- `CARDBOOK_REQUEST_LOGGING_ENABLED=True`.
- El status es `400` o mayor.
- O la duracion supera `CARDBOOK_SLOW_REQUEST_MS`.

Variables utiles:

```env
CARDBOOK_REQUEST_LOGGING_ENABLED=True
CARDBOOK_SLOW_REQUEST_MS=1000
CARDBOOK_REQUEST_LOG_EXCLUDED_PREFIXES=/static/,/media/
CARDBOOK_LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=WARNING
```

Cada linea incluye:

- `request_id`
- metodo HTTP
- path
- status
- duracion en milisegundos
- usuario autenticado si existe
- IP remota

## Health checks

Endpoints operativos:

- `/health/`
- `/health/ready/`

`/health/ready/` valida base de datos y configuracion sensible de produccion.

## Validacion

Desde la raiz:

```powershell
.\tool\production_gate.ps1 -SkipFlutter -SkipCollectstatic -SkipSmoke
```

Para revisar solo observabilidad:

```powershell
.\cb_env\Scripts\python.exe manage.py test cardbookweb
```

## Criterio de cierre

La fase queda lista cuando:

- Los tests de `cardbookweb` pasan.
- El gate de produccion incluye `cardbookweb`.
- Los logs permiten conectar errores web/API con un `X-Request-ID`.
