from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0008_businesscard_show_profile_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="hide_direct_contact_on_print",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="contact_cta_label",
            field=models.CharField(default="Contactanos", max_length=32),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="contact_cta_color",
            field=models.CharField(default="#003875", max_length=7),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="contact_cta_text_color",
            field=models.CharField(default="#ffffff", max_length=7),
        ),
    ]
