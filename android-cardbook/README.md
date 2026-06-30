# Cardbook Android

Aplicacion Android para Cardbook. La version actual usa un WebView nativo endurecido para entregar todas las funciones web existentes: autenticacion, dashboard, empresas, perfiles digitales, tarjetas de presentacion, Book, publicaciones y alianzas.

Version actual: `0.3.0` (`versionCode` 3), `minSdkVersion` 26, `targetSdkVersion` 35.

## Incluido ahora

- Splash profesional con logo Cardbook.
- Icono adaptativo Android.
- Tema visual con colores de Cardbook.
- Pantalla offline y manejo de errores principales.
- Cookies y sesion persistente.
- Enlaces externos bloqueados dentro del WebView y abiertos con apps nativas.
- Telefono, email, SMS, WhatsApp, mapas y websites con intents de Android.
- Compartir nativo cuando la web use `navigator.share`.
- Descarga de archivos, contactos `.vcf`, imagenes y QR con `DownloadManager`.
- Selector Android para subir fotos/archivos desde formularios web.
- Build manual con versionado y firma release opcional por variables de entorno.

## Desarrollo local

1. Ejecuta Django en tu maquina:

```bash
python manage.py runserver
```

2. Abre esta carpeta en Android Studio:

```text
android-cardbook/
```

3. En emulador Android usa esta base URL si haces una variante local:

```text
http://10.0.2.2:8000
```

4. Para generar el APK con Android Studio/Gradle:

```bash
./gradlew assembleDebug
```

5. Si no tienes Gradle configurado, usa el build manual incluido:

```powershell
.\build_apk.ps1
```

Ese script usa el Android SDK local y copia el APK final a:

```text
static/downloads/cardbook.apk
```

La pagina `/android/#build` muestra version, SDK, tamano y descarga.

## Firma release

El script firma con debug por defecto para pruebas. Para generar un APK release, define estas variables antes de ejecutar `build_apk.ps1`:

```powershell
$env:CARDBOOK_RELEASE_KEYSTORE="C:\ruta\cardbook-release.jks"
$env:CARDBOOK_RELEASE_ALIAS="cardbook"
$env:CARDBOOK_RELEASE_STOREPASS="tu-store-pass"
$env:CARDBOOK_RELEASE_KEYPASS="tu-key-pass"
$env:CARDBOOK_ANDROID_VERSION_CODE="4"
$env:CARDBOOK_ANDROID_VERSION_NAME="0.4.0"
.\build_apk.ps1
```

## Cambiar API para produccion

Edita `app/build.gradle.kts` o `MainActivity.java` y cambia la URL base por tu dominio HTTPS definitivo, por ejemplo:

```kotlin
buildConfigField("String", "CARDBOOK_API_BASE_URL", '"https://tudominio.com"')
```
