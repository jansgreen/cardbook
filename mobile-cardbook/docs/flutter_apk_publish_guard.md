# Publicacion segura del APK Flutter

La descarga publica de Cardbook solo debe servir el APK Flutter nativo.

## Regla actual

La vista `/android/download/` solo entrega `static/downloads/cardbook.apk` si tambien existe:

```text
static/downloads/cardbook.apk.json
```

Y esa metadata contiene:

```json
{
  "source": "flutter"
}
```

Ademas, el APK debe pesar al menos 5 MB. Esto evita publicar por accidente el APK WebView anterior, que pesaba menos de 1 MB.

## Generar APK Flutter publicable

Desde la raiz del proyecto:

```powershell
.\mobile-cardbook\tool\build_release.ps1
```

El script:

1. Ejecuta `flutter create .` si falta la carpeta Android.
2. Ejecuta `flutter pub get`.
3. Ejecuta `flutter analyze`.
4. Ejecuta `flutter test`.
5. Construye `app-release.apk`.
6. Copia el APK Flutter a `static/downloads/cardbook.apk`.
7. Crea `static/downloads/cardbook.apk.json`.

## Estado importante

Si Flutter no esta instalado en `PATH`, no se puede generar la APK nativa. En ese caso la web mostrara que la APK Flutter esta pendiente en vez de descargar el WebView anterior.

