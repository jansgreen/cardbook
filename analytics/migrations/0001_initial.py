import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CardClick",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("click_type", models.CharField(choices=[("phone", "Phone"), ("email", "Email"), ("website", "Website"), ("whatsapp", "WhatsApp"), ("social", "Social")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("card", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clicks", to="cards.digitalcard")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CardView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("source", models.CharField(blank=True, max_length=100, null=True)),
                ("language", models.CharField(blank=True, max_length=2, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("card", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="views", to="cards.digitalcard")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
