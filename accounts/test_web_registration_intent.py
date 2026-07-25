from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from referrals.models import AgentApplication, AgentProfile, Referral


class WebRegistrationIntentTests(TestCase):
    password = "StrongPassword123!"

    def register_payload(self, username="newuser", email="newuser@cardbook.test"):
        return {
            "username": username,
            "email": email,
            "first_name": "New",
            "last_name": "User",
            "phone_number": "+18095550100",
            "preferred_language": "es",
            "password1": self.password,
            "password2": self.password,
        }

    def test_register_requires_usage_selection_first(self):
        response = self.client.get(reverse("web-register"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("web-register-intent"))

    def test_company_usage_is_saved_on_registered_user(self):
        intent_response = self.client.post(reverse("web-register-intent"), {"usage": "company"})
        self.assertRedirects(intent_response, reverse("web-register"))

        response = self.client.post(reverse("web-register"), self.register_payload(username="companyuser"))

        self.assertRedirects(response, reverse("dashboard-home"))
        user = get_user_model().objects.get(username="companyuser")
        self.assertEqual(user.registration_intent, "company")

    def test_job_usage_is_saved_on_registered_user(self):
        intent_response = self.client.post(reverse("web-register-intent"), {"usage": "job"})
        self.assertRedirects(intent_response, reverse("web-register"))

        response = self.client.post(
            reverse("web-register"),
            self.register_payload(username="jobuser", email="jobuser@cardbook.test"),
        )

        self.assertRedirects(response, reverse("dashboard-white-card-job"))
        user = get_user_model().objects.get(username="jobuser")
        self.assertEqual(user.registration_intent, "job")

    def test_job_user_login_goes_directly_to_white_card_job(self):
        user = get_user_model().objects.create_user(
            username="joblogin",
            email="joblogin@cardbook.test",
            password=self.password,
            registration_intent="job",
        )

        response = self.client.post(
            reverse("web-login"),
            {"username": user.username, "password": self.password},
        )

        self.assertRedirects(response, reverse("dashboard-white-card-job"))

    def test_agent_without_referral_code_goes_to_application(self):
        response = self.client.post(reverse("web-register-intent"), {"usage": "agent"})

        self.assertRedirects(response, reverse("web-agent-application"))

    def test_agent_application_creates_pending_application_and_continues_to_register(self):
        response = self.client.post(
            reverse("web-agent-application"),
            {
                "full_name": "Ana Rivera",
                "email": "ana.agent@cardbook.test",
                "phone_number": "+18095550101",
                "city": "Paterson",
                "experience": "Ventas locales y soporte a pequenos negocios.",
                "reason": "Quiero representar Cardbook con empresas de mi ciudad.",
            },
        )

        self.assertRedirects(response, reverse("web-register"))
        self.assertTrue(AgentApplication.objects.filter(email="ana.agent@cardbook.test").exists())

        register_response = self.client.post(
            reverse("web-register"),
            self.register_payload(username="agentapp", email="ana.agent@cardbook.test"),
        )

        self.assertRedirects(register_response, reverse("dashboard-referrals"))
        user = get_user_model().objects.get(username="agentapp")
        self.assertEqual(user.registration_intent, "agent")

    def test_agent_user_login_goes_directly_to_referrals(self):
        user = get_user_model().objects.create_user(
            username="agentlogin",
            email="agentlogin@cardbook.test",
            password=self.password,
            registration_intent="agent",
        )

        response = self.client.post(
            reverse("web-login"),
            {"username": user.username, "password": self.password},
        )

        self.assertRedirects(response, reverse("dashboard-referrals"))

    def test_agent_referral_code_must_be_valid(self):
        response = self.client.post(
            reverse("web-register-intent"),
            {"usage": "agent", "referral_code": "AGT-FAKE"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este codigo de referido no existe o no esta activo.")

    def test_agent_with_valid_referral_code_creates_referral_after_register(self):
        agent_user = get_user_model().objects.create_user(
            username="agentowner",
            email="agentowner@cardbook.test",
            password=self.password,
        )
        AgentProfile.objects.create(user=agent_user, referral_code="AGT-VALID")

        intent_response = self.client.post(
            reverse("web-register-intent"),
            {"usage": "agent", "referral_code": "AGT-VALID"},
        )
        self.assertRedirects(intent_response, reverse("web-register"))

        register_response = self.client.post(
            reverse("web-register"),
            self.register_payload(username="referredagent", email="referredagent@cardbook.test"),
        )

        self.assertRedirects(register_response, reverse("dashboard-referrals"))
        user = get_user_model().objects.get(username="referredagent")
        self.assertEqual(user.registration_intent, "agent")
        self.assertTrue(Referral.objects.filter(referred_user=user, referral_code="AGT-VALID").exists())
