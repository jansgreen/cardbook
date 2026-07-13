# Fase 18 - Seguridad release Android

Esta fase endurece el proceso de build para que Cardbook no llegue a produccion con una firma debug accidental.

## Objetivo

- Crear upload keystore fuera del repositorio.
- Configurar `android/key.properties` local.
- Exigir firma real para builds Play Store.
- Verificar APK/AAB antes de publicar.

## Crear keystore

Desde `mobile-cardbook`:

```powershell
.\tool\create_upload_keystore.ps1
```

Por defecto crea:

```text
%USERPROFILE%\cardbook-secure\cardbook-upload-key.jks
android\key.properties
```

`android/key.properties` y archivos `.jks` estan ignorados por Git. No los subas.

## Build interno

Para publicar APK descargable desde la web:

```powershell
.\tool\build_release.ps1
```

Este build puede usar `debug:fallback` mientras sea solo prueba directa.

## Build Play Store

Para Google Play:

```powershell
.\tool\build_release.ps1 -AppBundle -RequireReleaseSigning
```

Si no existe keystore real, el build falla antes de generar el AAB.

## Auditoria estricta

```powershell
.\tool\release_audit.ps1 -StrictReleaseSigning
```

## Verificar APK publicado

```powershell
.\tool\verify_release_signing.ps1
```

Para exigir firma real:

```powershell
.\tool\verify_release_signing.ps1 -RequireReleaseSigning
```

## Variables de entorno para CI

Como alternativa a `android/key.properties`:

```powershell
$env:CARDBOOK_UPLOAD_STORE_FILE="C:\Users\jansg\cardbook-secure\cardbook-upload-key.jks"
$env:CARDBOOK_UPLOAD_STORE_PASSWORD="..."
$env:CARDBOOK_UPLOAD_KEY_ALIAS="cardbook-upload"
$env:CARDBOOK_UPLOAD_KEY_PASSWORD="..."
```

## Regla importante

Si `/android/version/` o `static/downloads/cardbook.apk.json` muestra:

```json
"signing": "debug:fallback"
```

ese artefacto es solo para pruebas internas. No debe enviarse a Google Play.
