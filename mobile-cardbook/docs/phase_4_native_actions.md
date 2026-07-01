# Fase 4 - Detalles y acciones nativas

Esta fase agrega la primera capa de interaccion movil real sobre los datos que ya vienen de la API.

## Acciones nativas

Se agrego `NativeActions` para abrir funciones del telefono:

- Llamadas con `tel:`
- Email con `mailto:`
- Websites con navegador externo
- WhatsApp con `wa.me`
- Mapas con Google Maps web
- Compartir con el sistema nativo de Android/iOS

## Pantallas nuevas

- `CompanyDetailScreen`
  - Muestra logo, nombre, categoria, descripcion, ubicacion e informacion de contacto.
  - Permite llamar, enviar email, abrir web, abrir mapa, compartir y abrir sitio publico.

- `CardDetailScreen`
  - Muestra perfil de negocio o tarjeta de presentacion.
  - Permite llamar, enviar email, abrir web, WhatsApp, compartir y abrir vista publica.

## Rutas nuevas

- `/companies/detail`
- `/cards/detail`

Las rutas reciben datos por `GoRouter.extra` desde las listas. Esto evita pedir otro endpoint antes de tener pantallas de detalle mas profundas.

## Pendiente

- Acciones reales de CRUD desde formularios Flutter.
- Pull-to-refresh.
- Descarga de contacto `.vcf`.
- Guardar QR o imagen en galeria.
- Permisos Android finales cuando se genere el proyecto con `flutter create .`.
