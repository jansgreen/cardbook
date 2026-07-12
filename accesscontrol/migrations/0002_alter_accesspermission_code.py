from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accesscontrol", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesspermission",
            name="code",
            field=models.CharField(max_length=120, unique=True),
        ),
    ]
