# Fase 10 - Build profesional

Esta fase prepara la app Flutter para builds debug, release APK y release AAB.

## Incluido

- Script PowerShell para debug:
  - `tool/build_debug.ps1`
- Script PowerShell para release:
  - `tool/build_release.ps1`
- Script Bash para release:
  - `tool/build_release.sh`
- Configuracion ejemplo:
  - `release_config.example.json`

## Requisito previo

Flutter debe estar instalado y disponible en `PATH`.

Despues de instalar Flutter, desde `mobile-cardbook` ejecuta:

```bash
flutter create .
flutter pub get
```

Eso generara las carpetas nativas `android/`, `ios/`, etc. No se deben crear a mano.

## Build debug

PowerShell:

```powershell
.\tool\build_debug.ps1
```

## Build release APK

PowerShell:

```powershell
.\tool\build_release.ps1
```

Bash:

```bash
./tool/build_release.sh
```

## Build release AAB

PowerShell:

```powershell
.\tool\build_release.ps1 -AppBundle
```

Bash:

```bash
./tool/build_release.sh https://cardbook-45cf0409dc07.herokuapp.com aab
```

## Configuracion Android pendiente tras `flutter create .`

En `android/app/build.gradle` o `android/app/build.gradle.kts` revisar:

- `namespace` / `applicationId`: `com.cardbook.app`
- `minSdk`: `26`
- `targetSdk`: `35`
- `versionCode`: `1`
- `versionName`: `0.1.0`

## Firma release

Pendiente de crear keystore privada. No se debe guardar la keystore real en Git.

Variables recomendadas:

- `CARD_BOOK_KEYSTORE_PATH`
- `CARD_BOOK_KEYSTORE_PASSWORD`
- `CARD_BOOK_KEY_ALIAS`
- `CARD_BOOK_KEY_PASSWORD`

## Salidas esperadas

- APK:
  - `build/app/outputs/flutter-apk/app-release.apk`
- AAB:
  - `build/app/outputs/bundle/release/app-release.aab`

## Publicacion interna

Cuando exista APK release, copiarlo al backend:

```powershell
Copy-Item mobile-cardbook\build\app\outputs\flutter-apk\app-release.apk static\downloads\cardbook.apk -Force
```

Luego actualizar en `web/views.py`:

- `ANDROID_VERSION_NAME`
- `ANDROID_VERSION_CODE`
- `ANDROID_TARGET_SDK`
