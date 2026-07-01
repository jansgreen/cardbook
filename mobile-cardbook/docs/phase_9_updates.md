# Fase 9 - Version y actualizaciones

Esta fase agrega consulta de version disponible desde la app Flutter.

## Incluido

- Version local centralizada en `AppVersion`.
- Repositorio `AppUpdateRepository`.
- Provider `appUpdateProvider`.
- Widget `UpdateStatusCard`.
- Integracion visual en Perfil.

## Endpoint usado

- `GET /android/version/`

## Datos soportados

- Version instalada.
- Version disponible.
- Codigo minimo soportado.
- `force_update`.
- URL directa de descarga.
- Pagina de descarga.
- Changelog.

## Comportamiento

- Si hay una version nueva, se muestra accion para descargar.
- Si no hay version nueva, se indica que la app esta actualizada.
- Si falla la consulta, se muestra boton para reintentar.
- La descarga abre el navegador o manejador externo del sistema.

## Pendiente

- Leer version automaticamente desde package metadata cuando se agregue `package_info_plus`.
- Bloquear uso si `force_update` o version no soportada.
- Dialog automatico al abrir la app.
- Integracion Play Store / App Store cuando existan releases publicos.
