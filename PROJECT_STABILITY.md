# Cardbook Project Stability

## Proyecto activo

Ruta activa de trabajo:

`C:\Users\jansg\OneDrive\Desktop\projects\python\cardbook`

Rama activa:

`stable/cardbook-core`

Remoto de produccion:

`heroku https://git.heroku.com/cardbook.git`

## Deploy a Heroku

El proyecto activo se despliega desde `stable/cardbook-core` hacia `main` en Heroku:

```bash
git push heroku stable/cardbook-core:main
```

No usar `git push heroku master`, porque este repositorio no usa rama `master`.

Si `git push heroku main` dice `Everything up-to-date` pero no ves cambios, verifica primero:

```bash
git branch --show-current
git log --oneline --decorate -3
git ls-remote --heads heroku
```

## Validaciones antes de push

```bash
cb_env\Scripts\python.exe manage.py check
cb_env\Scripts\python.exe manage.py makemigrations --dry-run --check
cb_env\Scripts\python.exe manage.py test ai_agents
```

Para una revision mas amplia:

```bash
cb_env\Scripts\python.exe manage.py test
```

## Release final

Dry run sin desplegar:

```bash
.\tool\release_heroku.ps1 -SkipFlutter -SkipCollectstatic -SkipSmokeBeforeDeploy
```

Deploy real controlado:

```bash
.\tool\release_heroku.ps1 -Deploy
```

## Archivos locales que no deben entrar al repo

- `cb_env/`
- `.env`
- `db.sqlite3`
- `media/`
- `staticfiles/`
- `*.log`
- `mobile-cardbook/.dart_tool/`
- `mobile-cardbook/build/`
- `android-cardbook/manual-build/`

## Notas de rama

La rama local `main` puede estar atrasada respecto a `stable/cardbook-core`. Para evitar confusiones, trabajar y desplegar desde `stable/cardbook-core` hasta que se decida formalmente unificar ramas.
