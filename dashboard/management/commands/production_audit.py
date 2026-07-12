import json
from dataclasses import asdict, dataclass
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor


@dataclass
class AuditItem:
    key: str
    label: str
    status: str
    message: str


class Command(BaseCommand):
    help = "Run Cardbook production readiness checks before deploy."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Return machine-readable JSON.")
        parser.add_argument("--strict", action="store_true", help="Fail when any error is found.")
        parser.add_argument("--fail-on-warnings", action="store_true", help="Treat warnings as failures.")
        parser.add_argument("--skip-db", action="store_true", help="Skip database and migration checks.")

    def handle(self, *args, **options):
        items = self.build_audit(skip_db=options["skip_db"])
        error_count = sum(1 for item in items if item.status == "error")
        warning_count = sum(1 for item in items if item.status == "warning")
        payload = {
            "success": error_count == 0 and (warning_count == 0 or not options["fail_on_warnings"]),
            "environment": settings.DEPLOY_ENV,
            "debug": settings.DEBUG,
            "version": settings.APP_VERSION,
            "errors": error_count,
            "warnings": warning_count,
            "checks": [asdict(item) for item in items],
        }

        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2))
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("Cardbook production audit"))
            self.stdout.write(f"Environment: {settings.DEPLOY_ENV}")
            self.stdout.write(f"Version: {settings.APP_VERSION}")
            for item in items:
                marker = self.marker_for(item.status)
                self.stdout.write(f"{marker} {item.label}: {item.message}")
            self.stdout.write("")
            self.stdout.write(f"Errors: {error_count} | Warnings: {warning_count}")

        should_fail = options["strict"] and error_count > 0
        should_fail = should_fail or (options["fail_on_warnings"] and (error_count > 0 or warning_count > 0))
        if should_fail:
            raise CommandError("Production audit failed.")

    def build_audit(self, skip_db=False):
        checks = [
            self.check_debug(),
            self.check_secret_key(),
            self.check_allowed_hosts(),
            self.check_csrf_origins(),
            self.check_security_flags(),
            self.check_staticfiles(),
            self.check_media_storage(),
            self.check_email(),
            self.check_stripe(),
            self.check_observability(),
            self.check_procfile(),
            self.check_requirements(),
        ]
        if not skip_db:
            checks.append(self.check_migrations())
        return checks

    def item(self, key, label, status, message):
        return AuditItem(key=key, label=label, status=status, message=message)

    def marker_for(self, status):
        if status == "ok":
            return self.style.SUCCESS("[OK]")
        if status == "warning":
            return self.style.WARNING("[WARN]")
        return self.style.ERROR("[ERROR]")

    def check_debug(self):
        if settings.DEBUG:
            return self.item("debug", "DEBUG", "error", "DJANGO_DEBUG esta activo; en produccion debe ser False.")
        return self.item("debug", "DEBUG", "ok", "DJANGO_DEBUG esta desactivado.")

    def check_secret_key(self):
        secret = settings.SECRET_KEY or ""
        weak = secret.startswith("django-insecure-") or len(secret) < 50 or len(set(secret)) < 8
        if weak:
            return self.item("secret_key", "SECRET_KEY", "error", "DJANGO_SECRET_KEY debe ser largo, privado y aleatorio.")
        return self.item("secret_key", "SECRET_KEY", "ok", "SECRET_KEY tiene longitud y variedad aceptables.")

    def check_allowed_hosts(self):
        hosts = set(settings.ALLOWED_HOSTS)
        if not hosts or "*" in hosts:
            return self.item("allowed_hosts", "ALLOWED_HOSTS", "error", "Define hosts concretos; no uses '*' en produccion.")
        return self.item("allowed_hosts", "ALLOWED_HOSTS", "ok", f"{len(hosts)} host(s) configurado(s).")

    def check_csrf_origins(self):
        if not settings.CSRF_TRUSTED_ORIGINS:
            return self.item("csrf", "CSRF trusted origins", "warning", "Configura DJANGO_CSRF_TRUSTED_ORIGINS para el dominio HTTPS publico.")
        insecure = [origin for origin in settings.CSRF_TRUSTED_ORIGINS if not origin.startswith("https://")]
        if insecure:
            return self.item("csrf", "CSRF trusted origins", "warning", "Hay origenes CSRF sin HTTPS.")
        return self.item("csrf", "CSRF trusted origins", "ok", f"{len(settings.CSRF_TRUSTED_ORIGINS)} origen(es) HTTPS configurado(s).")

    def check_security_flags(self):
        missing = []
        if not settings.SECURE_SSL_REDIRECT:
            missing.append("SECURE_SSL_REDIRECT")
        if not settings.SESSION_COOKIE_SECURE:
            missing.append("SESSION_COOKIE_SECURE")
        if not settings.CSRF_COOKIE_SECURE:
            missing.append("CSRF_COOKIE_SECURE")
        if settings.SECURE_HSTS_SECONDS <= 0:
            missing.append("SECURE_HSTS_SECONDS")
        if settings.X_FRAME_OPTIONS != "DENY":
            missing.append("X_FRAME_OPTIONS=DENY")
        if missing:
            return self.item("security_flags", "Security flags", "error", "Faltan: " + ", ".join(missing))
        return self.item("security_flags", "Security flags", "ok", "SSL, cookies seguras, HSTS y frame protection activos.")

    def check_staticfiles(self):
        static_root = Path(settings.STATIC_ROOT)
        backend = settings.STORAGES.get("staticfiles", {}).get("BACKEND", "")
        if "whitenoise" not in backend and not settings.DEBUG:
            return self.item("staticfiles", "Static files", "warning", "El backend staticfiles no parece usar WhiteNoise.")
        if not static_root.exists():
            return self.item("staticfiles", "Static files", "warning", "STATIC_ROOT aun no existe; ejecuta collectstatic en build/deploy.")
        return self.item("staticfiles", "Static files", "ok", "STATIC_ROOT existe y backend de estaticos configurado.")

    def check_media_storage(self):
        if not getattr(settings, "USE_S3_MEDIA_STORAGE", False):
            return self.item("media_storage", "Media storage", "error", "DJANGO_USE_S3_MEDIA_STORAGE esta apagado; Heroku no persiste uploads locales.")
        if not getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
            return self.item("media_storage", "Media storage", "error", "AWS_STORAGE_BUCKET_NAME es requerido para S3.")
        return self.item("media_storage", "Media storage", "ok", "S3 media storage configurado.")

    def check_email(self):
        backend = settings.EMAIL_BACKEND
        if backend.endswith(".console.EmailBackend"):
            return self.item("email", "Email", "warning", "EMAIL_BACKEND usa consola; no enviara correos reales.")
        if backend.endswith(".smtp.EmailBackend") and (not settings.EMAIL_HOST or settings.EMAIL_HOST == "localhost"):
            return self.item("email", "Email", "error", "EMAIL_HOST debe apuntar al proveedor SMTP real.")
        if not settings.DEFAULT_FROM_EMAIL or "localhost" in settings.DEFAULT_FROM_EMAIL:
            return self.item("email", "Email", "error", "DEFAULT_FROM_EMAIL debe usar un dominio real.")
        return self.item("email", "Email", "ok", "Email configurado para proveedor real.")

    def check_stripe(self):
        missing = []
        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            missing.append("STRIPE_SECRET_KEY")
        if not getattr(settings, "STRIPE_WEBHOOK_SECRET", ""):
            missing.append("STRIPE_WEBHOOK_SECRET")
        if missing:
            return self.item("stripe", "Stripe", "error", "Faltan variables: " + ", ".join(missing))
        return self.item("stripe", "Stripe", "ok", "Stripe y webhook secret configurados.")

    def check_observability(self):
        if not getattr(settings, "CARDBOOK_ENABLE_REQUEST_ID_HEADERS", True):
            return self.item("observability", "Observability", "warning", "X-Request-ID esta apagado; dejalo activo para rastrear errores.")
        return self.item("observability", "Observability", "ok", "X-Request-ID y logging configurables activos.")

    def check_procfile(self):
        procfile = settings.BASE_DIR / "Procfile"
        if not procfile.exists():
            return self.item("procfile", "Procfile", "error", "Procfile no existe.")
        content = procfile.read_text(encoding="utf-8", errors="ignore")
        missing = []
        if "web:" not in content or "gunicorn" not in content:
            missing.append("web gunicorn")
        if "release:" not in content or "migrate" not in content:
            missing.append("release migrate")
        if missing:
            return self.item("procfile", "Procfile", "warning", "Revisa entradas: " + ", ".join(missing))
        return self.item("procfile", "Procfile", "ok", "web dyno y release migrate configurados.")

    def check_requirements(self):
        requirements = settings.BASE_DIR / "requirements.txt"
        if not requirements.exists():
            return self.item("requirements", "Requirements", "error", "requirements.txt no existe.")
        content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        required = ["gunicorn", "whitenoise", "dj-database-url", "psycopg", "stripe", "django-storages", "boto3"]
        missing = [package for package in required if package not in content]
        if missing:
            return self.item("requirements", "Requirements", "error", "Faltan dependencias: " + ", ".join(missing))
        return self.item("requirements", "Requirements", "ok", "Dependencias criticas de produccion presentes.")

    def check_migrations(self):
        try:
            connection = connections[DEFAULT_DB_ALIAS]
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
        except Exception as exc:
            return self.item("migrations", "Migrations", "error", f"No se pudieron revisar migraciones: {exc.__class__.__name__}.")
        if plan:
            return self.item("migrations", "Migrations", "error", f"Hay {len(plan)} migracion(es) pendiente(s). Ejecuta migrate.")
        return self.item("migrations", "Migrations", "ok", "No hay migraciones pendientes.")
