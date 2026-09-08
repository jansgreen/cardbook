# Cardbook Mobile

Aplicacion Flutter nativa para Cardbook. Consume la API REST del backend Django y reemplazara gradualmente la APK WebView.

## Requisitos

- Flutter SDK 3.24 o superior.
- Dart 3.4 o superior.
- Android Studio con Android SDK.

## Primer arranque

```bash
cd mobile-cardbook
flutter create .
flutter pub get
flutter run --dart-define=CARDBOOK_API_BASE_URL=https://incardbook.com
```

Para desarrollo local con emulador Android:

```bash
flutter run --dart-define=CARDBOOK_API_BASE_URL=http://10.0.2.2:8000
```

## Backend esperado

La app inicia consultando:

```text
GET /api/v1/mobile/config/
POST /api/v1/accounts/login/
GET /api/v1/accounts/me/
GET /api/v1/mobile/dashboard/
```

El token se guarda con `flutter_secure_storage` y se envia como:

```text
Authorization: Bearer <access_token>
```

## Builds

Debug APK en PowerShell:

```powershell
.\tool\build_debug.ps1
```

Release APK:

```powershell
.\tool\build_release.ps1
```

Ese comando tambien publica el APK Flutter en `static/downloads/cardbook.apk` y crea la metadata que habilita `/android/download/`.

Release AAB para Play Store:

```powershell
.\tool\build_release.ps1 -AppBundle -RequireReleaseSigning
```

Antes de publicar en Play Store configura `android/key.properties` o las variables `CARDBOOK_UPLOAD_*`. Ver `docs/phase_15_play_store_release.md`.
Para crear y validar la firma release real, ver `docs/phase_18_release_security.md`.

Build completo de produccion, con APK y AAB firmados:

```powershell
.\tool\build_production.ps1
```

Este comando falla si no existe una firma release real. El APK interno puede existir con `debug:fallback`, pero Google Play requiere `release_signed=true`.

Crear upload keystore local:

```powershell
.\tool\create_upload_keystore.ps1
```

Auditoria estricta antes de Play Store:

```powershell
.\tool\release_audit.ps1 -StrictReleaseSigning
```

En Bash:

```bash
./tool/build_release.sh
./tool/build_release.sh https://incardbook.com aab true
```

Mas detalle en `docs/phase_10_release_build.md`.

## Auditoria pre-lanzamiento

```powershell
.\tool\release_audit.ps1
```

Este comando revisa Django, metadata de Google Play, paginas legales, endpoints publicos y entorno Flutter/Android.

## QA movil completo

```powershell
.\tool\mobile_qa.ps1 -BuildDebug
```

Para la matriz manual de pruebas base, ver `docs/phase_19_mobile_qa.md`.
Para el flujo real actualizado con tarjetas fisicas, OCR, borradores y build, ver `docs/phase_23_mobile_real_flow_qa.md`.

## Push notifications

La integracion FCM esta documentada en `docs/phase_20_push_notifications.md`.

Despues de configurar Firebase, agrega `android/app/google-services.json` y define `FCM_SERVER_KEY` en Heroku.

## Pulido UX

Los criterios y cambios de estados vacios/errores estan en `docs/phase_21_ux_polish.md`.

## Cierre de produccion movil

El flujo final de firma, APK, AAB y verificacion esta en `docs/phase_22_mobile_production.md`.

## Predeploy Heroku

```powershell
.\tool\predeploy_heroku.ps1
```

Este comando corre `manage.py check`, `collectstatic` y la auditoria de release antes de subir cambios a Heroku.

## Health checks

```text
/health/
/health/ready/
```

Estos endpoints ayudan a confirmar que Heroku esta ejecutando la version correcta y que la base de datos responde.

## Smoke test de produccion

```powershell
.\tool\smoke_heroku.ps1
```

Este comando revisa la URL publica despues del deploy: health checks, API raiz, pagina Android, version Android, privacidad y terminos.
