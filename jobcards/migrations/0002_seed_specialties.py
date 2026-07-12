from django.db import migrations
from django.utils.text import slugify


SPECIALTIES = [
    ("Plomeria", "Servicios"),
    ("Electricidad", "Servicios"),
    ("Desarrollo de Software", "Tecnologia"),
    ("Diseno Grafico", "Creatividad"),
    ("Construccion", "Servicios"),
    ("Cocina", "Hospitalidad"),
    ("Contabilidad", "Administracion"),
    ("Limpieza", "Servicios"),
    ("Soldadura", "Industria"),
    ("Mecanica", "Servicios"),
    ("Marketing", "Comercial"),
    ("Ventas", "Comercial"),
    ("Atencion al Cliente", "Comercial"),
    ("Enfermeria", "Salud"),
    ("Educacion", "Educacion"),
]


def seed_specialties(apps, schema_editor):
    Specialty = apps.get_model("jobcards", "Specialty")
    for name, category in SPECIALTIES:
        Specialty.objects.get_or_create(
            name=name,
            defaults={
                "category": category,
                "slug": slugify(name),
            },
        )


def unseed_specialties(apps, schema_editor):
    Specialty = apps.get_model("jobcards", "Specialty")
    Specialty.objects.filter(name__in=[name for name, _category in SPECIALTIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("jobcards", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_specialties, unseed_specialties),
    ]
