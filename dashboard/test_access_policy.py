from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from companies.models import Company
from dashboard.access_policy import dashboard_menu_for_user, default_dashboard_url_name
from referrals.models import AgentApplication, AgentProfile


class DashboardAccessPolicyTests(TestCase):
    password = "StrongPassword123!"

    def create_user(self, username, intent="", **extra):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@incardbook.test",
            password=self.password,
            registration_intent=intent,
            **extra,
        )

    def login(self, user):
        self.client.force_login(user)

    def menu_keys(self, user):
        return {item["key"] for item in dashboard_menu_for_user(user)}

    def sidebar_html(self, response):
        content = response.content.decode()
        start = content.index('<nav class="sidebar-nav"')
        end = content.index("</nav>", start)
        return content[start:end]

    def test_company_user_menu_excludes_white_card_and_referrals(self):
        user = self.create_user("companyuser", "company")

        keys = self.menu_keys(user)

        self.assertIn("companies", keys)
        self.assertIn("business_cards", keys)
        self.assertNotIn("white_card_job", keys)
        self.assertNotIn("referrals", keys)
        self.assertNotIn("finance", keys)
        self.assertNotIn("access", keys)

    def test_job_user_menu_is_limited_to_job_book_notifications_and_companies(self):
        user = self.create_user("jobuser", "job")

        self.assertEqual(
            self.menu_keys(user),
            {"companies", "white_card_job", "notifications", "book"},
        )

    def test_agent_menu_has_operational_features_but_not_finance_or_access(self):
        user = self.create_user("agentuser", "agent")

        keys = self.menu_keys(user)

        self.assertIn("referrals", keys)
        self.assertIn("white_card_job", keys)
        self.assertIn("companies", keys)
        self.assertNotIn("finance", keys)
        self.assertNotIn("access", keys)

    def test_existing_agent_profile_is_treated_as_agent(self):
        user = self.create_user("oldagent")
        AgentProfile.objects.create(user=user)

        keys = self.menu_keys(user)

        self.assertIn("referrals", keys)
        self.assertNotIn("finance", keys)
        self.assertNotIn("access", keys)

    def test_superuser_menu_has_finance_and_access(self):
        user = self.create_user("super", is_staff=True, is_superuser=True)

        keys = self.menu_keys(user)

        self.assertIn("finance", keys)
        self.assertIn("access", keys)
        self.assertIn("white_card_job", keys)
        self.assertIn("referrals", keys)

    def test_company_sidebar_hides_disallowed_items(self):
        user = self.create_user("companynav", "company")
        self.login(user)

        response = self.client.get(reverse("dashboard-home"))
        sidebar = self.sidebar_html(response)

        self.assertIn("Resumen", sidebar)
        self.assertIn("Empresas", sidebar)
        self.assertIn("Perfil del negocio", sidebar)
        self.assertIn("Presentacion", sidebar)
        self.assertNotIn("White Card Job", sidebar)
        self.assertNotIn("Referidos", sidebar)
        self.assertNotIn("Finanzas", sidebar)
        self.assertNotIn("Accesos", sidebar)

    def test_job_sidebar_shows_only_allowed_items(self):
        user = self.create_user("jobnav", "job")
        self.login(user)

        response = self.client.get(reverse("dashboard-book"))
        sidebar = self.sidebar_html(response)

        self.assertIn("Empresas", sidebar)
        self.assertIn("White Card Job", sidebar)
        self.assertIn("Book", sidebar)
        self.assertIn("Notificaciones", sidebar)
        self.assertNotIn("Resumen", sidebar)
        self.assertNotIn("Website Builder", sidebar)
        self.assertNotIn("Perfil del negocio", sidebar)
        self.assertNotIn("Presentacion", sidebar)
        self.assertNotIn("Referidos", sidebar)
        self.assertNotIn("Finanzas", sidebar)
        self.assertNotIn("Accesos", sidebar)

    def test_agent_sidebar_hides_finance_and_access(self):
        user = self.create_user("agentnav", "agent")
        self.login(user)

        response = self.client.get(reverse("dashboard-referrals"))
        sidebar = self.sidebar_html(response)

        self.assertIn("Referidos", sidebar)
        self.assertIn("White Card Job", sidebar)
        self.assertIn("Website Builder", sidebar)
        self.assertNotIn("Finanzas", sidebar)
        self.assertNotIn("Accesos", sidebar)

    def test_default_dashboard_url_changes_by_account_type(self):
        company_user = self.create_user("defaultcompany", "company")
        job_user = self.create_user("defaultjob", "job")
        agent_user = self.create_user("defaultagent", "agent")
        superuser = self.create_user("defaultsuper", is_staff=True, is_superuser=True)

        self.assertEqual(default_dashboard_url_name(company_user), "dashboard-home")
        self.assertEqual(default_dashboard_url_name(job_user), "dashboard-white-card-job")
        self.assertEqual(default_dashboard_url_name(agent_user), "dashboard-referrals")
        self.assertEqual(default_dashboard_url_name(superuser), "dashboard-home")

    def test_company_user_cannot_open_white_card_job_dashboard(self):
        user = self.create_user("companyblocked", "company")
        self.login(user)

        response = self.client.get(reverse("dashboard-white-card-job"))

        self.assertRedirects(response, reverse("dashboard-home"))

    def test_company_user_cannot_open_referrals_finance_or_access(self):
        user = self.create_user("companyforbidden", "company")
        self.login(user)

        forbidden_urls = [
            reverse("dashboard-referrals"),
            reverse("finance-dashboard"),
            reverse("dashboard-access-control"),
        ]

        for url in forbidden_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("dashboard-home"))

    def test_job_user_cannot_open_website_builder_dashboard(self):
        user = self.create_user("jobblocked", "job")
        self.login(user)

        response = self.client.get(reverse("dashboard-home"))

        self.assertRedirects(response, reverse("dashboard-white-card-job"))

    def test_job_user_cannot_open_company_operational_sections(self):
        user = self.create_user("jobsectionsblocked", "job")
        company = Company.objects.create(owner=self.create_user("ownerforjobsections"), name="Owner Co", is_active=True)
        self.login(user)

        forbidden_urls = [
            reverse("dashboard-card-create"),
            reverse("dashboard-business-card-create"),
            reverse("dashboard-analytics"),
            reverse("dashboard-referrals"),
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            reverse("dashboard-access-control"),
            reverse("finance-dashboard"),
        ]

        for url in forbidden_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("dashboard-white-card-job"))

    def test_job_user_can_open_allowed_sections(self):
        user = self.create_user("joballowedsections", "job")
        self.login(user)

        allowed_urls = [
            reverse("dashboard-companies"),
            reverse("dashboard-white-card-job"),
            reverse("dashboard-book"),
            reverse("dashboard-notifications"),
        ]

        for url in allowed_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_job_user_book_shows_free_collection_experience(self):
        user = self.create_user("jobbook", "job")
        self.login(user)

        response = self.client.get(reverse("dashboard-book"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gratis para candidatos")
        self.assertContains(response, "Guarda tarjetas y perfiles digitales")
        self.assertContains(response, "Guarda tarjetas que compartan contigo")
        self.assertNotContains(response, "Para contratar")

    def test_company_user_without_company_sees_company_next_step(self):
        user = self.create_user("companyempty", "company")
        self.login(user)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crea tu empresa para activar Cardbook")
        self.assertContains(response, reverse("dashboard-company-create"))

    def test_company_user_without_company_gets_profile_empty_state(self):
        user = self.create_user("companyprofileempty", "company")
        self.login(user)

        response = self.client.get(reverse("dashboard-cards"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crea una empresa antes de publicar perfiles")
        self.assertContains(response, reverse("dashboard-company-create"))

    def test_company_user_without_company_gets_business_card_empty_state(self):
        user = self.create_user("companybcardempty", "company")
        self.login(user)

        response = self.client.get(reverse("dashboard-business-cards"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crea una empresa antes de crear tarjetas")
        self.assertContains(response, reverse("dashboard-company-create"))

    def test_job_user_without_white_card_sees_next_step(self):
        user = self.create_user("jobempty", "job")
        self.login(user)

        response = self.client.get(reverse("dashboard-white-card-job"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crea tu White Card Job")
        self.assertContains(response, "#white-card-form")

    def test_agent_without_profile_sees_pending_application_state(self):
        user = self.create_user("agentpending", "agent")
        AgentApplication.objects.create(
            full_name="Agent Pending",
            email=user.email,
            reason="Quiero vender Cardbook.",
        )
        self.login(user)

        response = self.client.get(reverse("dashboard-referrals"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tu solicitud esta en revision")

    def test_agent_cannot_open_finance_or_access_dashboard(self):
        user = self.create_user("agentblocked", "agent")
        self.login(user)

        finance_response = self.client.get(reverse("finance-dashboard"))
        access_response = self.client.get(reverse("dashboard-access-control"))

        self.assertRedirects(finance_response, reverse("dashboard-referrals"))
        self.assertRedirects(access_response, reverse("dashboard-referrals"))

    def test_superuser_can_open_finance_and_access_dashboard(self):
        user = self.create_user("superallowed", is_staff=True, is_superuser=True)
        Company.objects.create(owner=user, name="Super Company", is_active=True)
        self.login(user)

        finance_response = self.client.get(reverse("finance-dashboard"))
        access_response = self.client.get(reverse("dashboard-access-control"))

        self.assertNotEqual(finance_response.status_code, 302)
        self.assertNotEqual(access_response.status_code, 302)
