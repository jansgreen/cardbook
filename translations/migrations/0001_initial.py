import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CardTranslation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(choices=[("es", "Spanish"), ("en", "English"), ("fr", "French"), ("pt", "Portuguese")], default="es", max_length=2)),
                ("full_name", models.CharField(max_length=255)),
                ("bio", models.TextField(blank=True, null=True)),
                ("services", models.TextField(blank=True, null=True)),
                ("address", models.TextField(blank=True, null=True)),
                ("custom_message", models.TextField(blank=True, null=True)),
                ("card", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translations", to="cards.digitalcard")),
            ],
            options={
                "ordering": ["card", "language"],
                "unique_together": {("card", "language")},
            },
        ),
    ]
