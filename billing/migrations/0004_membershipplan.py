from django.db import migrations, models


def create_default_membership_plans(apps, schema_editor):
    MembershipPlan = apps.get_model("billing", "MembershipPlan")
    plans = [
        {
            "key": "starter",
            "name": "Inicial",
            "description": "Para validar una presencia digital sencilla.",
            "features": "1 perfil digital\nQR publico\nBook basico",
            "unit_amount": "0.00",
            "currency": "USD",
            "billing_interval": "monthly",
            "is_free": True,
            "order": 10,
        },
        {
            "key": "business",
            "name": "Negocio",
            "description": "Para empresas que necesitan tarjetas, website y estadisticas.",
            "features": "Perfiles de negocio\nPresentaciones comerciales\nWebsite Builder",
            "unit_amount": "12.00",
            "currency": "USD",
            "billing_interval": "monthly",
            "is_free": False,
            "order": 20,
        },
        {
            "key": "team",
            "name": "Equipo",
            "description": "Para manejar mas usuarios, empresas y operaciones.",
            "features": "Equipo ampliado\nAccesos por rol\nSoporte prioritario",
            "unit_amount": "29.00",
            "currency": "USD",
            "billing_interval": "monthly",
            "is_free": False,
            "order": 30,
        },
    ]
    for plan in plans:
        defaults = plan.copy()
        key = defaults.pop("key")
        MembershipPlan.objects.get_or_create(key=key, defaults=defaults)


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0003_stripeconfiguration"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("features", models.TextField(blank=True, help_text="Una caracteristica por linea.")),
                ("unit_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("billing_interval", models.CharField(choices=[("monthly", "Monthly"), ("yearly", "Yearly")], default="monthly", max_length=20)),
                ("stripe_price_id", models.CharField(blank=True, max_length=255)),
                ("is_free", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["order", "unit_amount", "name"],
            },
        ),
        migrations.RunPython(create_default_membership_plans, migrations.RunPython.noop),
    ]
