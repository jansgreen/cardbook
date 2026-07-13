# Fase 15 - Produccion Android y Play Store

Esta fase prepara la app Flutter de Cardbook para builds de produccion, APK interno y AAB para Google Play.

## Firma release

La app soporta dos formas de configurar la firma real:

1. Archivo local `android/key.properties`.
2. Variables de entorno `CARDBOOK_UPLOAD_*`.

Nunca subas el keystore real ni `android/key.properties` al repositorio.

## Crear upload key local

Ejemplo PowerShell:

```powershell
keytool -genkeypair `
  -v `
  -keystore C:\Users\jansg\secure\cardbook-upload-key.jks `
  -storetype JKS `
  -keyalg RSA `
  -keysize 2048 `
  -validity 10000 `
  -alias cardbook-upload
```

Luego copia:

```powershell
Copy-Item .\android\key.properties.example .\android\key.properties
```

Edita `android/key.properties`:

```properties
storePassword=TU_PASSWORD
keyPassword=TU_PASSWORD
keyAlias=cardbook-upload
storeFile=C:\\Users\\jansg\\secure\\cardbook-upload-key.jks
```

## Build APK interno

Para descargar desde la web de Cardbook:

```powershell
.\tool\build_release.ps1
```

Ese comando publica:

```text
../static/downloads/cardbook.apk
../static/downloads/cardbook.apk.json
```

## Build AAB para Play Store

Para Play Store exige firma real:

```powershell
.\tool\build_release.ps1 -AppBundle -RequireReleaseSigning
```

Salida esperada:

```text
build/app/outputs/bundle/release/app-release.aab
```

## Variables de entorno alternativas

```powershell
$env:CARDBOOK_UPLOAD_STORE_FILE="C:\Users\jansg\secure\cardbook-upload-key.jks"
$env:CARDBOOK_UPLOAD_STORE_PASSWORD="TU_PASSWORD"
$env:CARDBOOK_UPLOAD_KEY_ALIAS="cardbook-upload"
$env:CARDBOOK_UPLOAD_KEY_PASSWORD="TU_PASSWORD"
```

## Metadata publica

`/android/version/` expone:

- version code
- version name
- tamano APK
- sha256
- tipo de build
- tipo de firma

Si `signing` muestra `debug:fallback`, esa build es solo interna y no debe enviarse a Play Store.
