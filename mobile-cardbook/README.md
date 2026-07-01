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
