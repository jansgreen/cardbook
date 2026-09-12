from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import ensure_default_permissions
from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_user
from websitebuilder.models import Page, Website
from websitebuilder.services import (
    can_manage_website_builder,
    can_publish_website_builder,
    create_starter_website,
    website_public_url,
    website_publish_status,
)


class WebsiteBuilderQualityTests(APITestCase):
    def test_default_permissions_create_website_editor_role(self):
        ensure_default_permissions()

        role = AccessRole.objects.get(name="Editor Website Builder")
        codes = set(role.permissions.values_list("code", flat=True))

        self.assertIn("websitebuilder.manage", codes)
        self.assertIn("websitebuilder.publish", codes)

    def test_access_grant_allows_user_to_manage_and_publish_website(self):
        ensure_default_permissions()
        owner = make_user("siteowner")
        editor = make_user("siteeditor")
        company = make_company(owner=owner)
        role = AccessRole.objects.get(name="Editor Website Builder")
        UserAccessGrant.objects.create(user=editor, company=company, role=role)

        self.assertTrue(can_manage_website_builder(editor, company))
        self.assertTrue(can_publish_website_builder(editor, company))

    def test_publish_status_blocks_incomplete_website(self):
        company = make_company(owner=make_user("draftowner"))
        website = Website.objects.create(company=company, title="Draft Site", is_published=False)

        status = website_publish_status(website)

        self.assertFalse(status["can_publish"])
        self.assertIn("Define una pagina principal.", status["issues"])

    def test_publish_status_allows_starter_website(self):
        company = make_company(owner=make_user("readyowner"))
        website = create_starter_website(company, publish=True)
        Page.objects.filter(website=website).update(is_published=True)

        status = website_publish_status(website)

        self.assertTrue(status["can_publish"])
        self.assertEqual(status["issues"], [])

    def test_public_site_accepts_company_slug(self):
        company = make_company(owner=make_user("companyslugowner"), name="La Costura de Dona Nancy")
        website = create_starter_website(company, publish=True)
        website.slug = "nancy-custom-site"
        website.save(update_fields=["slug", "updated_at"])

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": company.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, website.title)

    def test_public_site_has_share_preview_metadata(self):
        company = make_company(
            owner=make_user("sitemetaowner"),
            name="BlueNova Technologies",
            description="Soluciones digitales para empresas.",
        )
        website = create_starter_website(company, publish=True)
        website.meta_title = "BlueNova Website"
        website.save(update_fields=["meta_title", "updated_at"])

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug}), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta property="og:title" content="BlueNova Technologies">')
        self.assertContains(response, '<meta property="og:image" content="https://testserver/static/img/logo.png">')
        self.assertContains(response, '<meta property="og:description" content="Soluciones digitales para empresas.">')

    def test_public_site_redirects_unpublished_company_to_public_company_profile(self):
        company = make_company(owner=make_user("draftsiteowner"), name="Draft Public Business")
        create_starter_website(company, publish=False)

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": company.slug}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("public-company-detail", kwargs={"slug": company.slug}))

    def test_public_site_redirects_stale_card_website_to_business_card(self):
        owner = make_user("stalesiteowner")
        company = make_company(owner=owner, name="Nancy Alterations")
        profile = make_digital_card(user=owner, company=company)
        business_card = make_business_card(
            profile=profile,
            display_name="Neyda Mendez",
            website="https://incardbook.com/site/la-costura-de-dona-nancy/",
        )

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": "la-costura-de-dona-nancy"}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("public-business-card", kwargs={"slug": business_card.slug}))

    @override_settings(
        ALLOWED_HOSTS=["testserver", ".incardbook.test"],
        CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="incardbook.test",
    )
    def test_public_site_renders_from_subdomain_host(self):
        company = make_company(owner=make_user("subdomainowner"), name="Alta Costura")
        website = create_starter_website(company, publish=True)

        response = self.client.get("/", HTTP_HOST=f"{website.subdomain}.incardbook.test")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, website.title)

    @override_settings(
        ALLOWED_HOSTS=["testserver", ".incardbook.test"],
        CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="incardbook.test",
    )
    def test_public_site_subdomain_keeps_static_paths_unmodified(self):
        company = make_company(owner=make_user("staticpathowner"), name="Static Path Co")
        website = create_starter_website(company, publish=True)

        response = self.client.get("/static/css/style.css", HTTP_HOST=f"{website.subdomain}.incardbook.test")

        self.assertNotEqual(response.request["PATH_INFO"], f"/site/{website.subdomain}/static/css/style.css/")

    @override_settings(
        ALLOWED_HOSTS=["testserver", "incardbook.test", ".incardbook.test"],
        CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="incardbook.test",
    )
    def test_website_public_url_prefers_subdomain_on_base_domain(self):
        company = make_company(owner=make_user("prettyurlowner"), name="Pretty URL Co")
        website = create_starter_website(company, publish=True)
        request = self.client.get("/", HTTP_HOST="incardbook.test", secure=True).wsgi_request

        public_url = website_public_url(request, website)

        self.assertEqual(public_url, f"https://{website.subdomain}.incardbook.test/")

    @override_settings(CARDBOOK_RESERVED_SUBDOMAINS=("www", "api", "dashboard"))
    def test_dashboard_builder_updates_website_subdomain(self):
        owner = make_user("identityowner")
        company = make_company(owner=owner, name="Identity Company")
        website = create_starter_website(company, publish=True)
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {
                "action": "update_identity",
                "title": "Alta Costura",
                "subdomain": "Alta Costura",
                "domain": "",
            },
        )

        website.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(website.title, "Alta Costura")
        self.assertEqual(website.subdomain, "alta-costura")

    @override_settings(CARDBOOK_RESERVED_SUBDOMAINS=("www", "api", "dashboard"))
    def test_dashboard_builder_rejects_reserved_subdomain(self):
        owner = make_user("reservedowner")
        company = make_company(owner=owner, name="Reserved Company")
        website = create_starter_website(company, publish=True)
        original_subdomain = website.subdomain
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {
                "action": "update_identity",
                "title": website.title,
                "subdomain": "www",
                "domain": "",
            },
        )

        website.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(website.subdomain, original_subdomain)
