# Fase 3 - Integracion nativa con API

Esta fase conecta las pantallas principales de Flutter con endpoints reales de Cardbook.

## Endpoints usados

- `GET /api/v1/companies/`
- `GET /api/v1/companies/recommendations/`
- `GET /api/v1/cards/`
- `GET /api/v1/cards/business-cards/`
- `GET /api/v1/book/`
- `GET /api/v1/alliances/`

## Pantallas conectadas

- Empresas: lista empresas propias y sugeridas.
- Tarjetas: lista perfiles de negocio y tarjetas de presentacion.
- Book: lista negocios guardados.
- Notificaciones: lista alianzas y solicitudes.

## Infraestructura Flutter

- `api_response.dart` centraliza lectura de respuestas paginadas.
- Repositorios por modulo usan `Dio` y el token guardado.
- Pantallas usan `FutureProvider` de Riverpod.
- Estados de loading, error y empty usan `AsyncStateView`.
- Login restaura sesion si existe token local.

## Pendiente para fase posterior

- Crear formularios nativos de CRUD.
- Acciones nativas para compartir tarjetas.
- Detalles de empresa y tarjeta.
- Refrescar listas con pull-to-refresh.
- Logout visible desde perfil.
