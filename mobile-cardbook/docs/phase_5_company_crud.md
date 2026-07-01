# Fase 5 - CRUD nativo inicial

Esta fase agrega CRUD nativo para Empresas desde Flutter.

## Incluido

- Crear empresa desde `/companies/form`.
- Editar empresa desde el detalle.
- Eliminar empresa con confirmacion.
- Refrescar `companiesProvider` y `recommendedCompaniesProvider` despues de cambios.
- Formulario visual integrado al sistema oscuro de Cardbook.

## Campos soportados

- Nombre
- Descripcion
- Categoria
- Servicios
- Telefono
- Email
- Website
- Direccion
- Ciudad
- Region

## API usada

- `POST /api/v1/companies/`
- `PATCH /api/v1/companies/{id}/`
- `DELETE /api/v1/companies/{id}/`

## Pendiente

- Subida de logo con multipart.
- CRUD nativo de perfiles de negocio.
- CRUD nativo de tarjetas de presentacion.
- Formularios con selectores y validaciones mas profundas.
- Actualizar el detalle en pantalla despues de editar sin volver a listar.
