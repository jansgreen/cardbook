# Visual QA Checklist

Fase 11 cubre ajustes finales de UX visual antes del cierre de produccion.

## Superficies revisadas

- Home publico.
- Directorio de empresas.
- Tarjetas de presentacion en grid.
- White Card Jobs publicas.
- Websites publicados dentro del marketplace.
- Dashboard y modulos criticos mediante el production gate.

## Ajustes aplicados

- Limpieza de mojibake visible en el directorio publico.
- Separadores ASCII en conteos y metadatos para evitar problemas de encoding.
- Margen mas consistente en `container-fluid` del directorio.
- QR de tarjetas de negocio mas grande y estable para escaneo.
- Refuerzo responsive para tarjetas de negocio en pantallas pequenas.
- Alturas y wraps mas seguros para nombres largos, emails y websites.

## Regla de QA visual

Antes de deploy revisar manualmente:

- `/`
- `/companies/`
- `/dashboard/`
- `/dashboard/companies/`
- `/dashboard/business-cards/`
- `/dashboard/white-card-job/`
- `/dashboard/website-builder/`

Breakpoints minimos:

- 390px mobile.
- 768px tablet.
- 1366px laptop.
- 1920px desktop.

## Validacion automatica

```powershell
.\cb_env\Scripts\python.exe manage.py test web.tests_mvp_flow cardbookweb
.\tool\production_gate.ps1 -SkipFlutter -SkipCollectstatic -SkipSmoke
```

## Criterio de cierre

La fase queda lista cuando no hay texto mojibake visible, los QR se pueden escanear en el grid, y las tarjetas no se rompen en mobile ni desktop.
