# Cardbook Android

Aplicacion Android nativa para Cardbook. Consume la API REST del proyecto Django y cubre las areas principales de la plataforma: autenticacion, empresas, perfiles digitales, Book, publicaciones y alianzas.

## Desarrollo local

1. Ejecuta Django en tu maquina:

```bash
python manage.py runserver
```

2. Abre esta carpeta en Android Studio:

```text
android-cardbook/
```

3. En emulador Android usa esta base URL:

```text
http://10.0.2.2:8000
```

4. Para generar el APK:

```bash
./gradlew assembleDebug
```

5. Copia el APK generado a:

```text
static/downloads/cardbook.apk
```

La pagina `/android/` del sitio web servira esa descarga desde el home.

## Cambiar API para produccion

Edita `app/build.gradle.kts` y cambia `CARDBOOK_API_BASE_URL` por tu dominio HTTPS, por ejemplo:

```kotlin
buildConfigField("String", "CARDBOOK_API_BASE_URL", '"https://tudominio.com"')
```
