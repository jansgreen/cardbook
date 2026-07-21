import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from ai_agents.models import AIAgent
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from forms_builder.models import FormDefinition, FormSubmission
from jobcards.models import WhiteCardJob
from websitebuilder.models import Website


class Command(BaseCommand):
    help = "Generate a safe operational snapshot without exposing personal data."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Return machine-readable JSON.")

    def handle(self, *args, **options):
        payload = self.build_snapshot()
        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("Cardbook operational snapshot"))
        self.stdout.write(f"Environment: {payload['environment']}")
        self.stdout.write(f"Version: {payload['version']}")
        self.stdout.write(f"Generated at: {payload['generated_at']}")
        self.stdout.write("")
        for section, values in payload["counts"].items():
            self.stdout.write(self.style.SQL_FIELD(section))
            for key, value in values.items():
                self.stdout.write(f"  {key}: {value}")

    def build_snapshot(self):
        User = get_user_model()
        return {
            "success": True,
            "service": "cardbook",
            "environment": settings.DEPLOY_ENV,
            "version": settings.APP_VERSION,
            "commit": settings.RELEASE_COMMIT[:12] if settings.RELEASE_COMMIT else "unknown",
            "generated_at": timezone.now().isoformat(),
            "database": {
                "engine": connection.vendor,
                "name": str(connection.settings_dict.get("NAME", "")),
            },
            "storage": {
                "media_backend": settings.STORAGES.get("default", {}).get("BACKEND", ""),
                "static_backend": settings.STORAGES.get("staticfiles", {}).get("BACKEND", ""),
                "s3_media_enabled": bool(getattr(settings, "USE_S3_MEDIA_STORAGE", False)),
            },
            "counts": {
                "accounts": {
                    "users": User.objects.count(),
                    "active_users": User.objects.filter(is_active=True).count(),
                    "staff_users": User.objects.filter(is_staff=True).count(),
                },
                "companies": {
                    "companies": Company.objects.count(),
                    "active_companies": Company.objects.filter(is_active=True).count(),
                },
                "cards": {
                    "digital_profiles": DigitalCard.objects.count(),
                    "active_digital_profiles": DigitalCard.objects.filter(is_active=True).count(),
                    "business_cards": BusinessCard.objects.count(),
                    "active_business_cards": BusinessCard.objects.filter(is_active=True).count(),
                    "white_card_jobs": WhiteCardJob.objects.count(),
                    "active_white_card_jobs": WhiteCardJob.objects.filter(is_active=True).count(),
                },
                "websites": {
                    "websites": Website.objects.count(),
                    "published_websites": Website.objects.filter(is_published=True).count(),
                },
                "forms": {
                    "forms": FormDefinition.objects.count(),
                    "active_forms": FormDefinition.objects.filter(is_active=True).count(),
                    "submissions": FormSubmission.objects.count(),
                },
                "ai_agents": {
                    "agents": AIAgent.objects.count(),
                    "active_agents": AIAgent.objects.filter(is_active=True).count(),
                },
            },
        }
