# Fase 19 - QA movil completo

Esta fase define el proceso minimo para validar Cardbook Flutter antes de entregar un APK interno o un AAB para Play Store.

## QA automatizado

Desde `mobile-cardbook`:

```powershell
.\tool\mobile_qa.ps1
```

Incluye:

- `python manage.py check`
- tests del BFF movil
- tests de soporte
- `/health/`
- `/api/v1/mobile/config/`
- `/android/version/`
- `flutter pub get`
- `flutter analyze --no-fatal-infos`
- `flutter test`
- `flutter devices`

Build debug:

```powershell
.\tool\mobile_qa.ps1 -BuildDebug
```

Build release interno y verificacion:

```powershell
.\tool\mobile_qa.ps1 -BuildRelease
```

Instalar en un dispositivo Android conectado:

```powershell
.\tool\mobile_qa.ps1 -BuildDebug -InstallOnDevice
```

## Checklist manual en Android real

1. Login con usuario existente.
2. Registro de usuario nuevo.
3. Dashboard carga resumen, empresas y publicaciones.
4. Empresas: listar, crear, editar y abrir detalle.
5. Perfiles de negocio: crear, editar y compartir.
6. Tarjetas de presentacion: crear, editar, ver QR y compartir.
7. Book: guardar y abrir contactos guardados.
8. White Card Jobs: crear, editar, desactivar y compartir.
9. Website Builder: listar websites y abrir vista publica.
10. Marketplace: buscar empresas, perfiles y white cards.
11. Alianzas: solicitar, aceptar/rechazar si aplica.
12. Notificaciones: listar y marcar leidas.
13. Soporte: crear ticket y verlo en tickets recientes.
14. Diagnostico: health, readiness, sesion API y APK publicado.
15. Compartir nativo: WhatsApp, email, copy link y share sheet.
16. NFC: abrir boton NFC y validar permiso/compatibilidad.
17. Camara/galeria: subir imagen en formularios.
18. Offline: apagar red, abrir pantallas cacheadas, volver a conectar.
19. Actualizacion: verificar que `/android/version/` detecte version nueva.
20. Cierre de sesion y re-login.

## Criterios de salida

- Cero errores en `flutter analyze`.
- Tests Django moviles en verde.
- Tests Flutter en verde.
- APK instala en emulador o telefono real.
- Los flujos principales no muestran pantallas rotas.
- Si es Play Store, `release_signed` debe ser `true`.

## Riesgos conocidos

- `release_signed=false` es aceptable solo para APK interno.
- NFC depende del hardware del telefono.
- Push notifications todavia pertenece a una fase posterior.
- Algunos plugins reportan advertencia futura de Kotlin Gradle Plugin; no rompe el build actual.
