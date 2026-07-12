from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accesscontrol", "0002_alter_accesspermission_code"),
        ("cards", "0006_businesscard_name_font_businesscard_name_size_and_more"),
        ("companies", "0002_company_category_company_city_company_region_and_more"),
        ("referrals", "0002_alter_commission_options_commission_approved_by_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentCardSale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "sale_type",
                    models.CharField(
                        choices=[("business_profile", "Business profile"), ("business_presentation", "Business presentation card")],
                        max_length=40,
                    ),
                ),
                ("gross_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("commission_percentage", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5)),
                ("commission_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("currency", models.CharField(default="USD", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("commissioned", "Commissioned"), ("cancelled", "Cancelled")],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "access_grant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_card_sales",
                        to="accesscontrol.useraccessgrant",
                    ),
                ),
                ("agent", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="card_sales", to="referrals.agentprofile")),
                (
                    "business_card",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_sales",
                        to="cards.businesscard",
                    ),
                ),
                (
                    "commission",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="card_sale",
                        to="referrals.commission",
                    ),
                ),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="agent_card_sales", to="companies.company")),
                (
                    "created_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="agent_card_sales_created", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "digital_card",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_sales",
                        to="cards.digitalcard",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="agentcardsale",
            index=models.Index(fields=["agent", "status"], name="referrals_a_agent_i_be6550_idx"),
        ),
        migrations.AddIndex(
            model_name="agentcardsale",
            index=models.Index(fields=["company", "created_at"], name="referrals_a_company_690b12_idx"),
        ),
        migrations.AddConstraint(
            model_name="agentcardsale",
            constraint=models.UniqueConstraint(
                condition=models.Q(("digital_card__isnull", False)),
                fields=("digital_card", "sale_type"),
                name="unique_agent_sale_per_profile",
            ),
        ),
        migrations.AddConstraint(
            model_name="agentcardsale",
            constraint=models.UniqueConstraint(
                condition=models.Q(("business_card__isnull", False)),
                fields=("business_card", "sale_type"),
                name="unique_agent_sale_per_business_card",
            ),
        ),
    ]
