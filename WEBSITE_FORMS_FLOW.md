# Website Builder + Forms Builder

Fase 4 conecta las paginas empresariales creadas desde Website Builder con formularios administrables desde Forms Builder.

## Flujo principal

1. La empresa administra su website desde el dashboard.
2. La empresa crea formularios desde Forms Builder.
3. Cada formulario define email receptor, mensaje de exito y campos activos.
4. Un formulario puede adjuntarse a una seccion del website.
5. La seccion cambia a `contact_form` y conserva en `settings.form_id` el formulario seleccionado.
6. La pagina publica renderiza estructura HTML5 y el formulario embebido.
7. El envio publico crea `FormSubmission` y envia email al receptor configurado.

## Estructura HTML5

El Website Builder usa etiquetas semanticas desde el modelo `Section.html_tag`:

- `header` para encabezados de pagina o seccion.
- `nav` para navegacion secundaria cuando aplique.
- `main` como contenedor principal unico del template publico.
- `section` para bloques tematicos.
- `article` para contenido independiente.
- `aside` para contenido complementario.
- `footer` para pie de pagina.

## Garantia actual

La prueba `FormsBuilderTests.test_form_can_be_embedded_in_public_website_section` cubre:

- Creacion de website publicado.
- Creacion de formulario y campos.
- Adjuntar formulario a una seccion.
- Render publico del formulario integrado.
- Envio publico con persistencia y email.
