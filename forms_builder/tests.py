from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from companies.models import Company
from forms_builder.models import FormDefinition, FormField, FormSubmission


class FormsBuilderTests(TestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username="owner", email="owner@example.com", password="pass12345")
        self.company = Company.objects.create(owner=self.user, name="Acme Forms", email="sales@example.com")

    def test_owner_can_create_form_and_field(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard-form-builder-create", kwargs={"company_id": self.company.id}),
            {
                "name": "Contacto",
                "slug": "contacto",
                "recipient_email": "sales@example.com",
                "success_message": "Recibido",
                "is_active": "on",
            },
        )
        form_definition = FormDefinition.objects.get(company=self.company, slug="contacto")
        self.assertRedirects(response, reverse("dashboard-form-builder-detail", kwargs={"company_id": self.company.id, "form_id": form_definition.id}))

        response = self.client.post(
            reverse("dashboard-form-field-create", kwargs={"company_id": self.company.id, "form_id": form_definition.id}),
            {
                "label": "Email",
                "field_type": FormField.EMAIL,
                "is_required": "on",
                "is_active": "on",
                "order": "1",
            },
        )
        self.assertRedirects(response, reverse("dashboard-form-builder-detail", kwargs={"company_id": self.company.id, "form_id": form_definition.id}))
        self.assertEqual(form_definition.fields.count(), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_public_submission_is_saved_and_emailed(self):
        form_definition = FormDefinition.objects.create(
            company=self.company,
            name="Contacto",
            slug="contacto",
            recipient_email="sales@example.com",
        )
        field = FormField.objects.create(form=form_definition, label="Email", field_type=FormField.EMAIL, order=1)
        response = self.client.post(
            reverse("forms-builder-public-submit", kwargs={"company_slug": self.company.slug, "form_slug": form_definition.slug}),
            {f"field_{field.id}": "lead@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        submission = FormSubmission.objects.get(form=form_definition)
        self.assertEqual(submission.sender_email, "lead@example.com")
        self.assertTrue(submission.email_sent)
        self.assertEqual(len(mail.outbox), 1)
