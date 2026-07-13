# Fase 22 - Cierre de produccion movil

Esta fase deja Cardbook Android preparado para una salida real: APK interno para descarga directa y AAB firmado para Google Play.

## Estado actual

- Version movil: `0.1.3+4`.
- APK publico: `static/downloads/cardbook.apk`.
- Metadata APK: `static/downloads/cardbook.apk.json`.
- AAB Play Store: `static/downloads/cardbook.aab`.
- Metadata AAB: `static/downloads/cardbook.aab.json`.
- Endpoint de version: `/android/version/`.
- Pagina publica: `/android/#build`.

## Firma release obligatoria

Para produccion real, configura una de estas opciones:

1. `mobile-cardbook/android/key.properties`.
2. Variables de entorno:
   - `CARDBOOK_UPLOAD_STORE_FILE`
   - `CARDBOOK_UPLOAD_STORE_PASSWORD`
   - `CARDBOOK_UPLOAD_KEY_ALIAS`
   - `CARDBOOK_UPLOAD_KEY_PASSWORD`

Crear keystore local:

```powershell
.\tool\create_upload_keystore.ps1
```

## Build interno

Genera y publica el APK descargable desde la web:

```powershell
.\tool\build_release.ps1
```

Este comando puede producir `debug:fallback` si no hay keystore. Eso sirve para pruebas internas, no para Play Store.

## Build Play Store

Genera y publica el AAB firmado:

```powershell
.\tool\build_release.ps1 -AppBundle -RequireReleaseSigning
```

## Build completo de produccion

Cuando exista firma release real:

```powershell
.\tool\build_production.ps1
```

Este comando:

1. Verifica que exista firma release.
2. Genera APK release firmado.
3. Genera AAB release firmado.
4. Verifica el APK publicado con metadata y `apksigner` si esta disponible.

## Criterio de salida

Antes de publicar en Play Store:

- `/android/version/` debe mostrar `release_signed: true`.
- `/android/version/` debe mostrar `aab_available: true`.
- `/android/version/` debe mostrar `play_store_ready: true`.
- `/android/#build` debe mostrar `Listo para Play Store`.
- `.\tool\release_audit.ps1 -StrictReleaseSigning` debe terminar sin fallos.

## Nota importante

Si el APK muestra:

```json
"signing": "debug:fallback"
```

la app todavia es una build interna. Android puede instalarla manualmente, pero no debe subirse a Google Play.
