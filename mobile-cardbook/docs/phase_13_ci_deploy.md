# Fase 13 - CI y predeploy

Esta fase agrega validacion automatica para evitar publicar cambios incompletos del backend o de la app Flutter.

## Archivos agregados

- `.github/workflows/cardbook-ci.yml`
- `mobile-cardbook/tool/predeploy_heroku.ps1`

## CI

El workflow `Cardbook CI` ejecuta:

- Instalacion de dependencias Python.
- `python manage.py check`.
- `python manage.py collectstatic --noinput`.
- `flutter create .` dentro de `mobile-cardbook`.
- `flutter pub get`.
- `flutter analyze`.
- `flutter test`.

Se ejecuta en:

- Push a `main`.
- Pull request a `main`.
- Ejecucion manual desde GitHub Actions.

## Predeploy Heroku local

Antes de subir a Heroku:

```powershell
.\mobile-cardbook\tool\predeploy_heroku.ps1
```

Con URL publica personalizada:

```powershell
.\mobile-cardbook\tool\predeploy_heroku.ps1 -PublicBaseUrl "https://tu-dominio.com"
```

Si `collectstatic` ya se ejecuto y solo quieres revisar:

```powershell
.\mobile-cardbook\tool\predeploy_heroku.ps1 -SkipCollectstatic
```

## Flujo recomendado

1. Ejecutar `predeploy_heroku.ps1`.
2. Corregir cualquier `FAIL`.
3. Hacer commit.
4. Desplegar:

```powershell
git push heroku main
heroku run python manage.py migrate --app cardbook
heroku open --app cardbook
```

5. Verificar:

```text
/privacy/
/terms/
/android/
/android/version/
```

## Nota

Los `404` detectados en Heroku para paginas nuevas normalmente significan que el codigo local aun no fue desplegado o que el dyno esta ejecutando una version anterior.

