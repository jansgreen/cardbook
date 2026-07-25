# Fase 23 - QA movil real y preparacion de build

Esta fase valida que la app Flutter nativa de Cardbook funcione como cliente real de la API antes de generar un APK/AAB para entrega interna o Play Store.

## Objetivo

Confirmar en un telefono o emulador Android que los flujos principales de Cardbook funcionan de punta a punta:

- Autenticacion y permisos por tipo de usuario.
- Empresas, perfiles de negocio y tarjetas de presentacion.
- White Card Job para usuarios que buscan trabajo.
- Tarjetas fisicas importadas, OCR, borradores y publicacion.
- Book, compartir, QR, NFC y acciones nativas.
- Cache/offline y diagnostico.

## QA automatizado

Desde la raiz del proyecto:

```powershell
.\mobile-cardbook\tool\mobile_qa.ps1 -SkipRemoteSmoke
```

Con smoke remoto contra Heroku:

```powershell
.\mobile-cardbook\tool\mobile_qa.ps1
```

Build debug:

```powershell
.\mobile-cardbook\tool\mobile_qa.ps1 -BuildDebug
```

Build release interno:

```powershell
.\mobile-cardbook\tool\mobile_qa.ps1 -BuildRelease
```

Instalar en Android conectado:

```powershell
.\mobile-cardbook\tool\mobile_qa.ps1 -BuildDebug -InstallOnDevice
```

El script cubre:

- `python manage.py check`
- tests `mobile`
- tests `cards`
- tests `jobcards`
- tests `support`
- tests `pushnotifications`
- `/health/`
- `/api/v1/mobile/config/`
- `/android/version/`
- `flutter pub get`
- `flutter analyze --no-fatal-infos`
- `flutter test`
- `flutter devices`

## Matriz manual por usuario

### Usuario empresa

1. Iniciar sesion.
2. Confirmar menu permitido: empresas, website builder, perfil del negocio, presentacion, book, notificaciones.
3. Crear empresa.
4. Editar empresa.
5. Crear perfil de negocio.
6. Crear tarjeta de presentacion.
7. Importar tarjeta fisica desde camara.
8. Ejecutar OCR/asimilar datos.
9. Guardar borrador.
10. Salir y restaurar borrador.
11. Publicar borrador.
12. Abrir detalle de tarjeta.
13. Ver frente/reverso importado.
14. Ampliar imagen con zoom.
15. Compartir enlace publico.
16. Copiar enlace publico.
17. Guardar tarjeta en Book desde otra cuenta.

### Usuario que busca trabajo

1. Registrarse con intencion `buscar trabajo`.
2. Confirmar menu permitido: White Card Job, empresas, book, notificaciones.
3. Crear White Card Job.
4. Seleccionar categoria laboral.
5. Importar tarjeta laboral fisica.
6. Ejecutar OCR/asimilar datos.
7. Guardar borrador laboral.
8. Salir y restaurar borrador laboral.
9. Publicar borrador laboral.
10. Abrir lista de White Card Jobs.
11. Ver badge `Tarjeta fisica importada`.
12. Abrir preview de tarjeta fisica.
13. Ampliar frente/reverso con zoom.
14. Compartir perfil publico.
15. Copiar enlace publico.
16. Desactivar White Card Job.

### Agente Cardbook

1. Iniciar sesion como agente.
2. Confirmar acceso a empresas, tarjetas, website builder, book, referidos y funcionalidades de agente.
3. Confirmar que no ve finanzas ni access control.
4. Crear tarjeta bajo Cardbook si tiene permiso.
5. Revisar comisiones/referidos si el modulo esta disponible.

### Superusuario

1. Confirmar acceso completo.
2. Confirmar que ve finanzas.
3. Confirmar que ve access control.
4. Confirmar que puede revisar agentes y permisos.

## Pruebas nativas Android

1. Camara: capturar foto de perfil.
2. Camara: capturar frente/reverso de tarjeta fisica.
3. Galeria: seleccionar imagen existente.
4. Share sheet: compartir perfil o tarjeta.
5. WhatsApp: compartir enlace si esta instalado.
6. Email: abrir cliente de correo.
7. Telefono: abrir marcador.
8. Mapas: abrir direccion.
9. NFC: verificar compatibilidad y mensajes de permiso.
10. Offline: apagar red, abrir pantallas cacheadas y restaurar borradores.
11. Actualizacion: confirmar `/android/version/`.

## Checklist antes de build

- `flutter analyze` sin errores.
- `flutter test` sin errores.
- `python manage.py test mobile cards jobcards support pushnotifications` en verde.
- Migraciones aplicadas.
- `static/downloads/cardbook.apk` corresponde a Flutter, no WebView antiguo.
- `static/downloads/cardbook.apk.json` existe.
- `/android/version/` reporta version, SHA256, tamano y `source=flutter`.
- Para Play Store: `release_signed=true` y AAB firmado.

## Criterios de salida

- Un usuario empresa puede completar el ciclo empresa -> tarjeta -> compartir.
- Un usuario job puede completar el ciclo White Card -> OCR -> borrador -> publicar -> compartir.
- El Book guarda elementos compartidos.
- Los permisos del menu coinciden con `registration_intent`.
- Las imagenes subidas se ven desde Heroku o el storage configurado.
- El APK instala y abre en Android real.

## Riesgos pendientes

- Si Heroku no muestra imagenes de media, se necesita storage externo persistente como S3/Cloudinary.
- Google ML Kit OCR depende de calidad de imagen, luz y enfoque.
- NFC depende del hardware del telefono.
- Firma debug no sirve para Play Store.
