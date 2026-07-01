# Fase 12 - Auditoria pre-lanzamiento

Esta fase agrega un auditor de lanzamiento para revisar el estado del backend, la app movil, metadatos de tienda y endpoints publicos.

## Script

- `tool/release_audit.ps1`

## Que valida

- Existe `pubspec.yaml`.
- Existe `release_config.example.json`.
- Existe metadata de Google Play en `store/google-play`.
- Existe borrador de Data Safety.
- Existen templates de privacidad y terminos.
- Ejecuta `python manage.py check`.
- Verifica si Flutter y Dart estan en `PATH`.
- Verifica `ANDROID_HOME`.
- Consulta endpoints publicos:
  - `/privacy/`
  - `/terms/`
  - `/android/version/`

## Uso

Desde la raiz del proyecto:

```powershell
.\mobile-cardbook\tool\release_audit.ps1
```

Con URL publica personalizada:

```powershell
.\mobile-cardbook\tool\release_audit.ps1 -PublicBaseUrl "https://tu-dominio.com"
```

## Interpretacion

- `FAIL`: problema que debe corregirse antes de publicar.
- `WARN`: pendiente o condicion externa, como Flutter no instalado.
- `OK`: verificacion correcta.

## Pendiente

- Ejecutar auditoria despues de instalar Flutter.
- Ejecutar auditoria contra dominio final.
- Agregar revision de screenshots cuando existan assets finales.
- Agregar validacion de archivo AAB despues del primer build release.
