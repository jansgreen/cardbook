from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from companies.models import Company
from forms_builder.models import FormDefinition, FormField, FormSubmission
from websitebuilder.services import create_starter_website


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

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_form_can_be_embedded_in_public_website_section(self):
        website = create_starter_website(self.company, publish=True)
        website.pages.update(is_published=True)
        page = website.pages.get(is_homepage=True)
        section = page.layout.sections.get(section_type="cta")
        form_definition = FormDefinition.objects.create(
            company=self.company,
            name="Solicitud de servicio",
            slug="solicitud",
            recipient_email="sales@example.com",
            success_message="Solicitud recibida.",
        )
        name_field = FormField.objects.create(form=form_definition, label="Nombre", field_type=FormField.TEXT, order=1)
        email_field = FormField.objects.create(form=form_definition, label="Email", field_type=FormField.EMAIL, order=2)
        message_field = FormField.objects.create(form=form_definition, label="Mensaje", field_type=FormField.TEXTAREA, order=3)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard-form-attach-section", kwargs={"company_id": self.company.id, "form_id": form_definition.id}),
            {"section_id": section.id},
        )
        self.assertRedirects(response, reverse("dashboard-form-builder-detail", kwargs={"company_id": self.company.id, "form_id": form_definition.id}))

        section.refresh_from_db()
        self.assertEqual(section.section_type, "contact_form")
        self.assertEqual(section.settings["form_id"], form_definition.id)

        public_url = reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug})
        response = self.client.get(public_url)
        self.assertContains(response, "<main", html=False)
        self.assertContains(response, reverse("forms-builder-public-submit", kwargs={"company_slug": self.company.slug, "form_slug": form_definition.slug}))
        self.assertContains(response, f"field_{name_field.id}")
        self.assertContains(response, f"field_{email_field.id}")
        self.assertContains(response, f"field_{message_field.id}")

        response = self.client.post(
            reverse("forms-builder-public-submit", kwargs={"company_slug": self.company.slug, "form_slug": form_definition.slug}),
            {
                f"field_{name_field.id}": "Maria Lead",
                f"field_{email_field.id}": "maria@example.com",
                f"field_{message_field.id}": "Necesito una cotizacion.",
                "next": public_url,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("form_status=sent", response["Location"])
        self.assertIn(f"form_id={form_definition.id}", response["Location"])

        submission = FormSubmission.objects.get(form=form_definition)
        self.assertEqual(submission.sender_name, "Maria Lead")
        self.assertEqual(submission.sender_email, "maria@example.com")
        self.assertTrue(submission.email_sent)
        self.assertEqual(len(mail.outbox), 1)
