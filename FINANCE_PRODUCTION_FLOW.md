# Finanzas y Billing

Fase 5 deja el modulo financiero operable desde dashboard y API.

## Dashboard

Las rutas `/dashboard/finance/` usan `templates/dashboard/finance/base_finance.html`, que extiende `dashboard/base_dashboard.html`. Esto evita que el usuario caiga en respuestas de API REST cuando entra desde el panel.

Secciones disponibles:

- Resumen financiero.
- Ingresos.
- Suscripciones.
- Empresas.
- Agentes.
- Comisiones.
- Pagos.
- Reembolsos.
- Reportes CSV.
- Auditoria.

## Reembolsos

Los pagos pueden reembolsarse desde `/dashboard/finance/payments/`.

Modos:

- Stripe configurado: crea el refund real usando `stripe.Refund.create`.
- Modo manual habilitado: registra el refund localmente para operaciones internas.
- Sin Stripe y sin modo manual: bloquea el reembolso y registra evento de auditoria si se intenta procesar.

Variables relacionadas:

- `STRIPE_SECRET_KEY`
- `STRIPE_ALLOW_MANUAL_REFUNDS`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_CUSTOMER_PORTAL_RETURN_URL`

## Portal de cliente

`/api/v1/billing/customer-portal/` crea una sesion de Stripe Customer Portal cuando la empresa tiene `stripe_customer_id` y Stripe esta configurado.

## Garantia actual

La suite `financial_analytics` cubre:

- Formulas de MRR, ARR y revenue neto.
- Permisos de API y dashboard.
- Render de paginas financieras con sesion web.
- Reembolsos manuales desde API y dashboard.
- Customer Portal con Stripe mockeado.
- Webhooks Stripe con firma, idempotencia y sincronizacion de pagos/refunds.
- Exportaciones CSV.
