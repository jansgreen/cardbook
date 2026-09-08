from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0007_businesscard_is_physical_card_imported_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="show_profile_photo",
            field=models.BooleanField(default=True),
        ),
    ]
