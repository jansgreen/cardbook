# Media Storage on Heroku

Las imagenes subidas por usuarios no se deben tratar igual que los archivos `static`.

## Problema

En Heroku, el filesystem del dyno es efimero. Eso significa:

- Los archivos dentro de `media/` no son persistentes.
- Al reiniciar o redeployar, Heroku puede borrar uploads locales.
- Django solo sirve `media/` automaticamente cuando `DEBUG=True`.

Por eso logos, fotos de perfil, websites y tarjetas pueden verse rotos en produccion si no hay storage externo.

## Solucion beta temporal

Para que las imagenes subidas se vean mientras pruebas:

```powershell
heroku config:set DJANGO_SERVE_MEDIA_FILES=True --app cardbook
```

Luego redeploy:

```powershell
.\tool\release_heroku.ps1 -Deploy -AllowReadinessWarnings
```

Limitacion: esto solo sirve archivos que existan dentro del dyno actual. No garantiza persistencia despues de restart.

## Solucion real de produccion

Configurar S3 compatible:

```powershell
heroku config:set DJANGO_USE_S3_MEDIA_STORAGE=True --app cardbook
heroku config:set AWS_ACCESS_KEY_ID=... --app cardbook
heroku config:set AWS_SECRET_ACCESS_KEY=... --app cardbook
heroku config:set AWS_STORAGE_BUCKET_NAME=... --app cardbook
heroku config:set AWS_S3_REGION_NAME=... --app cardbook
```

Opcional con dominio/CDN:

```powershell
heroku config:set AWS_S3_CUSTOM_DOMAIN=media.tu-dominio.com --app cardbook
```

## Nota importante

Las imagenes que subiste localmente en `C:\Users\jansg\...\media` no existen automaticamente en Heroku. Debes:

- Re-subirlas desde la web ya desplegada.
- Migrarlas a S3.
- Incluir assets demo en `static/` si son imagenes fijas del proyecto.
