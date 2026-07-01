# Fase 6 - CRUD nativo de tarjetas

Esta fase agrega CRUD nativo para los dos tipos de tarjetas de Cardbook.

## Perfiles de negocio

Ruta:

- `/cards/digital/form`

API:

- `POST /api/v1/cards/`
- `PATCH /api/v1/cards/{id}/`
- `DELETE /api/v1/cards/{id}/`

Campos iniciales:

- Empresa
- Cargo
- Telefono
- Email
- Website
- WhatsApp
- LinkedIn
- Instagram

## Tarjetas de presentacion

Ruta:

- `/cards/business/form`

API:

- `POST /api/v1/cards/business-cards/`
- `PATCH /api/v1/cards/business-cards/{id}/`
- `DELETE /api/v1/cards/business-cards/{id}/`

Campos iniciales:

- Perfil de negocio
- Nombre visible
- Cargo
- Empresa
- Telefono
- Email
- Website
- Direccion
- Frase corta
- Servicios

## Flujo

- Desde Tarjetas se puede crear perfil o tarjeta de presentacion.
- Desde el detalle se puede editar.
- Desde el detalle se puede eliminar con confirmacion.
- Las listas se refrescan despues de guardar o eliminar.

## Pendiente

- Subida de foto de perfil.
- Selector visual de fuente y tamano.
- Personalizacion QR.
- Colores de tarjeta.
- Vista previa en tiempo real antes de guardar.
