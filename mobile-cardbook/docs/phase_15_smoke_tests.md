# Fase 15 - Smoke tests de produccion

Esta fase agrega pruebas rapidas post-deploy para confirmar que Heroku esta sirviendo la version correcta de Cardbook.

## Script local

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1
```

Con version esperada:

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1 -ExpectedVersion "0.14.0"
```

Si todavia no desplegaste y quieres ver advertencias sin fallar:

```powershell
.\mobile-cardbook\tool\smoke_heroku.ps1 -AllowDeploymentPending
```

## Que valida

- `/health/`
- `/health/ready/`
- `/api/v1/`
- `/android/version/`
- `/`
- `/android/`
- `/privacy/`
- `/terms/`

## GitHub Actions

Se agrego el workflow manual:

```text
.github/workflows/cardbook-smoke.yml
```

Desde GitHub Actions puedes ejecutarlo indicando:

- URL publica.
- Version esperada.

## Uso recomendado

1. Ejecutar predeploy local.
2. Desplegar a Heroku.
3. Ejecutar smoke test.
4. Si todo responde `OK`, probar login, registro y dashboard manualmente.

