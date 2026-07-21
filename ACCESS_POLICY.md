# Cardbook Access Policy

## Capas de acceso

Cardbook usa dos capas:

1. `CompanyMember`: acceso estructural a una empresa.
2. `UserAccessGrant`: permisos finos por empresa, rol y grupo.

## Roles de empresa

`CompanyMember` controla el acceso general:

- `owner`: control total de la empresa.
- `admin`: administra empresa, miembros, contenido y servicios.
- `manager`: accede a la empresa y opera contenido, pero no administra accesos criticos.
- `staff`: acceso operativo limitado.

`owner` y `admin` se consideran administradores de empresa para `can_manage_company`.

## Permisos finos

Permisos creados por defecto desde `ensure_default_permissions()`:

- `access.manage`: CRUD de roles, grupos y asignaciones.
- `companies.manage_content`: contenido empresarial.
- `cards.create_profile`: perfiles de negocio.
- `cards.create_business_card.cardbook`: tarjetas bajo Cardbook para agentes.
- `websitebuilder.manage`: crear y editar sitios.
- `websitebuilder.publish`: publicar/despublicar sitios.
- `ai_agents.manage`: configurar, entrenar y revisar agentes IA.
- `sales.earn_commission`: marcar usuario como agente comisionable.

## Roles finos incluidos

- `Agente Cardbook`: puede crear tarjetas bajo Cardbook y recibir comision.
- `Editor Website Builder`: puede administrar y publicar websites.
- `Administrador de agentes IA`: puede administrar agentes IA en empresas asignadas.

## Reglas por modulo

Empresas:

- Owner/admin pueden editar empresa.
- Manager/staff pueden acceder si son miembros activos.

Tarjetas:

- Owner/admin/member autorizado puede crear perfiles segun `profile_creation_companies`.
- Agente con `cards.create_business_card.cardbook` puede crear tarjetas bajo la empresa asignada.

Website Builder:

- Owner/admin o grant `websitebuilder.manage` puede editar.
- Owner/admin o grant `websitebuilder.publish` puede publicar.

Forms Builder:

- Usa el permiso operativo de Website Builder: `websitebuilder.manage`.

Agentes IA:

- Owner/admin o grant `ai_agents.manage` puede configurar, entrenar y gestionar leads del agente.
- Lectura de agentes se limita a empresas accesibles o asignadas por grant IA.

Finanzas:

- Usa permisos Django nativos definidos en `financial_analytics.permissions.PERMISSION_MAP`.
- Superusuario conserva acceso total.

## Regla practica

Si un usuario necesita una funcion especifica sin control completo de la empresa, usar `UserAccessGrant`.

Si un usuario debe administrar la empresa completa, usar `CompanyMember` como `owner` o `admin`.

