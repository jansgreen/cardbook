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
flutter run --dart-define=CARDBOOK_API_BASE_URL=https://cardbook-45cf0409dc07.herokuapp.com
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

Release AAB para Play Store:

```powershell
.\tool\build_release.ps1 -AppBundle
```

En Bash:

```bash
./tool/build_release.sh
./tool/build_release.sh https://cardbook-45cf0409dc07.herokuapp.com aab
```

Mas detalle en `docs/phase_10_release_build.md`.

## Auditoria pre-lanzamiento

```powershell
.\tool\release_audit.ps1
```

Este comando revisa Django, metadata de Google Play, paginas legales, endpoints publicos y entorno Flutter/Android.

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
