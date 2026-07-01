# Fase 7 - Book y alianzas nativas

Esta fase agrega interacciones de red empresarial desde Flutter.

## Book

API:

- `POST /api/v1/book/`
- `DELETE /api/v1/book/{id}/`

Incluido:

- Guardar empresa desde el detalle.
- Quitar empresa guardada desde Book.
- Refrescar lista de Book despues de guardar o quitar.

## Alianzas

API:

- `POST /api/v1/alliances/`
- `POST /api/v1/alliances/{id}/accepted/`
- `POST /api/v1/alliances/{id}/rejected/`

Incluido:

- Solicitar alianza desde el detalle de empresa.
- Elegir empresa propia como solicitante.
- Aceptar solicitudes pendientes.
- Rechazar solicitudes pendientes.
- Refrescar lista de alianzas despues de responder.

## Pendiente

- Mostrar si una empresa ya esta guardada en Book.
- Ocultar acciones que no apliquen a empresas propias.
- Mejorar mensajes de error del backend en pantalla.
- Filtros de alianzas por pendiente, aceptada y rechazada.
