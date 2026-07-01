# Cardbook Mobile Design System

Fase 2 define la capa visual base para la app Flutter nativa.

## Estilo

- Tema oscuro profesional.
- Gradientes azul, violeta y tinta.
- Cards tipo cristal con bordes suaves.
- Botones compactos y tactiles.
- Navegacion inferior flotante.
- Iconografia Material para evitar caracteres rotos en Android.

## Tokens principales

- Fondo: `AppGradients.page`
- Accion primaria: `AppGradients.primary`
- Panel: `AppColors.panel`
- Panel alto: `AppColors.panelHigh`
- Texto principal: `AppColors.text`
- Texto secundario: `AppColors.muted`
- Acentos: `AppColors.blue`, `AppColors.purple`, `AppColors.gold`, `AppColors.green`

## Componentes

- `BrandHeader`: logo y marca Cardbook.
- `GlassCard`: contenedor principal para secciones.
- `MetricCard`: estadisticas compactas.
- `CompanyTile`: fila de empresa con logo, descripcion y rating.
- `PostPreviewCard`: preview de publicacion empresarial.
- `StatusBadge`: etiqueta visual para estados y categorias.
- `FeaturePlaceholder`: pantalla base para modulos pendientes.
- `AppBottomNav`: navegacion inferior de la app.

## Regla de encoding

La app evita caracteres decorativos pegados como texto. Para estrellas, checkmarks, notificaciones y acciones se usan `Icons.*` de Flutter. Esto previene errores visuales de mojibake cuando un WebView o un build maneja mal el encoding.
