# Fase 20 - Notificaciones push

Esta fase prepara Cardbook para push notifications en Android con Firebase Cloud Messaging.

## Backend

Endpoints protegidos por JWT:

```text
GET  /api/v1/push/devices/
POST /api/v1/push/devices/
POST /api/v1/push/devices/disable/
POST /api/v1/push/test/
```

Cada dispositivo guarda:

- usuario
- token FCM
- plataforma
- device id
- version de app
- estado activo/inactivo

Cuando Cardbook crea una notificacion interna de referidos/finanzas/agentes, tambien intenta enviar push al usuario.

Si `FCM_SERVER_KEY` no esta configurado, el envio se marca como `skipped` y no rompe el flujo.

## Variables Heroku

Para activar envio real:

```bash
heroku config:set FCM_SERVER_KEY="TU_SERVER_KEY" --app cardbook
```

Luego:

```bash
heroku run python manage.py migrate --app cardbook
```

## Flutter

Paquetes agregados:

```yaml
firebase_core
firebase_messaging
```

La app:

- Inicializa Firebase de forma defensiva.
- Pide permiso desde la pantalla Notificaciones.
- Registra el token en `/api/v1/push/devices/`.
- Actualiza el token si Firebase lo rota.
- Permite enviar push de prueba desde la app.

## Android

Permiso agregado:

```xml
android.permission.POST_NOTIFICATIONS
```

## Firebase pendiente

Para push real necesitas agregar:

```text
mobile-cardbook/android/app/google-services.json
```

Ese archivo debe venir desde Firebase Console y no debe contenerse como ejemplo con credenciales reales.

## QA

```powershell
.\tool\mobile_qa.ps1 -BuildDebug
```

Prueba manual:

1. Abrir Notificaciones.
2. Tocar Activar.
3. Aceptar permiso Android.
4. Verificar `/api/v1/push/devices/`.
5. Tocar Prueba.
6. Confirmar delivery en admin `PushDeliveryLog`.
