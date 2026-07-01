# Fase 8 - Perfil y sesion

Esta fase separa Perfil de Book y agrega gestion basica de cuenta.

## Incluido

- Nueva ruta `/profile`.
- Nueva ruta `/profile/edit`.
- Bottom nav apunta a Perfil en vez de Book.
- Book queda accesible desde Perfil.
- Lectura de perfil desde `GET /api/v1/accounts/me/`.
- Edicion de perfil con `PATCH /api/v1/accounts/profile/`.
- Logout nativo con intento de blacklist en backend y limpieza local de tokens.

## Campos editables

- Nombre
- Apellido
- Email
- Telefono
- Idioma preferido

## Pendiente

- Subida de avatar.
- Cambio de contrasena.
- Eliminar cuenta.
- Preferencias de notificaciones.
- Mostrar version instalada y version disponible.
