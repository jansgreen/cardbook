# Flutter Mobile

Fase 7 refuerza la app Flutter nativa como cliente real de la API REST de Cardbook.

## Estado actual

La app Flutter vive en `mobile-cardbook/` y consume el backend Django mediante `Dio` y JWT:

- Login y registro nativos.
- Empresas.
- Perfiles de negocio.
- Tarjetas de presentacion.
- Book.
- White Card Jobs.
- Marketplace.
- Websites.
- Alianzas.
- Notificaciones.
- Soporte.
- Acciones nativas: compartir, llamadas, email, WhatsApp, mapas y NFC.

## Diagnostico movil

La pantalla `/diagnostics` valida desde la app:

- `/health/`
- `/health/ready/`
- `/api/v1/mobile/config/`
- `/api/v1/accounts/me/`
- `/api/v1/mobile/dashboard/`
- `/android/version/`

Tambien muestra:

- Version instalada.
- Package name.
- API base.
- Web publica.
- Si existen tokens locales.

Esto ayuda a confirmar rapidamente si un fallo viene de la app, de la sesion, de Heroku, de la API o del APK publicado.

## Regla visual

La app evita separadores Unicode decorativos en texto operativo. Se usan separadores ASCII como `|` para prevenir mojibake en builds Android o entornos con encoding inconsistente.

## Comandos de validacion

Desde `mobile-cardbook/`:

```powershell
flutter analyze
flutter test
```

Desde la raiz Django:

```powershell
cb_env\Scripts\python.exe manage.py check
cb_env\Scripts\python.exe manage.py test mobile
```

## Prueba manual recomendada

1. Ejecutar backend local o usar Heroku.
2. Abrir la app en emulador.
3. Iniciar sesion.
4. Ir a `Menu > Diagnostico`.
5. Hacer pull-to-refresh.
6. Confirmar que `Sesion API` y `Dashboard movil` esten OK.
