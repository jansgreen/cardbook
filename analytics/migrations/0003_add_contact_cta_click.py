from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0002_alter_cardclick_click_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cardclick",
            name="click_type",
            field=models.CharField(
                choices=[
                    ("contact_cta_click", "Contact CTA click"),
                    ("contact_reveal", "Contact reveal"),
                    ("phone_click", "Phone click"),
                    ("whatsapp_click", "WhatsApp click"),
                    ("email_click", "Email click"),
                    ("website_click", "Website click"),
                    ("quote_request", "Quote request"),
                    ("appointment_request", "Appointment request"),
                    ("directions_click", "Directions click"),
                    ("message_click", "Message click"),
                    ("social_click", "Social click"),
                    ("phone", "Phone legacy"),
                    ("email", "Email legacy"),
                    ("website", "Website legacy"),
                    ("whatsapp", "WhatsApp legacy"),
                    ("social", "Social legacy"),
                ],
                max_length=32,
            ),
        ),
    ]
