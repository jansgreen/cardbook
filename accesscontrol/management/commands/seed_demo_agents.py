from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import ensure_default_permissions
from companies.models import Company
from memberships.models import CompanyMember


AGENTS = [
    ("agent_demo_1", "agent.demo1@cardbook.test", "Amelia", "Torres", Decimal("12.50")),
    ("agent_demo_2", "agent.demo2@cardbook.test", "Bruno", "Castillo", Decimal("15.00")),
    ("agent_demo_3", "agent.demo3@cardbook.test", "Clara", "Mendoza", Decimal("10.00")),
    ("agent_demo_4", "agent.demo4@cardbook.test", "Diego", "Rivas", Decimal("18.00")),
    ("agent_demo_5", "agent.demo5@cardbook.test", "Elena", "Suarez", Decimal("20.00")),
]


class Command(BaseCommand):
    help = "Crea 5 usuarios demo agentes y los asigna al rol Agente Cardbook."

    def handle(self, *args, **options):
        User = get_user_model()
        ensure_default_permissions()
        owner = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_active=True).first()
        if not owner:
            self.stderr.write("No hay usuarios para asignar como owner de Cardbook.")
            return

        with transaction.atomic():
            cardbook, _ = Company.objects.get_or_create(
                name="Cardbook",
                defaults={
                    "owner": owner,
                    "category": "Tecnologia",
                    "city": "Santo Domingo",
                    "region": "Distrito Nacional",
                    "services": "Tarjetas digitales, perfiles empresariales, agentes comerciales",
                    "description": "Empresa principal de la plataforma Cardbook.",
                    "website": "https://cardbook.local",
                    "is_active": True,
                },
            )
            if cardbook.owner_id != owner.id and owner.is_superuser:
                cardbook.owner = owner
                cardbook.save(update_fields=["owner", "updated_at"])
            CompanyMember.objects.get_or_create(
                company=cardbook,
                user=cardbook.owner,
                defaults={"role": CompanyMember.ROLE_OWNER},
            )

            role = AccessRole.objects.get(name="Agente Cardbook")
            created = 0
            for username, email, first_name, last_name, commission in AGENTS:
                user, was_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "is_active": True,
                    },
                )
                if was_created:
                    user.set_password("CardbookAgent123!")
                    user.save()
                    created += 1
                else:
                    changed = False
                    for field, value in {
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    }.items():
                        if getattr(user, field) != value:
                            setattr(user, field, value)
                            changed = True
                    if changed:
                        user.save(update_fields=["email", "first_name", "last_name"])

                UserAccessGrant.objects.update_or_create(
                    user=user,
                    company=cardbook,
                    role=role,
                    defaults={
                        "commission_percent": commission,
                        "notes": "Agente demo creado para pruebas comerciales.",
                        "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Agentes demo listos. Nuevos usuarios creados: {created}."))
        self.stdout.write("Password demo: CardbookAgent123!")
