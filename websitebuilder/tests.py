from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import ensure_default_permissions
from cardbookweb.test_utils import make_business_card, make_company, make_digital_card, make_user
from websitebuilder.models import Block, Component, Page, Website
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
    def test_public_site_renders_updated_subdomain_without_hyphens(self):
        company = make_company(owner=make_user("plaintokensubdomainowner"), name="Candido Mecanica Automotriz")
        website = create_starter_website(company, publish=True)
        website.subdomain = "candidomecanicaautomotriz"
        website.save(update_fields=["subdomain", "updated_at"])

        response = self.client.get("/", HTTP_HOST="candidomecanicaautomotriz.incardbook.test")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, website.title)

    @override_settings(
        ALLOWED_HOSTS=["testserver", ".incardbook.test"],
        CARDBOOK_PUBLIC_SITE_BASE_DOMAIN="incardbook.test",
    )
    def test_subdomain_does_not_capture_global_companies_path(self):
        company = make_company(owner=make_user("reservedpathowner"), name="Candido Mecanica Automotriz")
        website = create_starter_website(company, publish=True)
        website.subdomain = "candidomecanicaautomotriz"
        website.save(update_fields=["subdomain", "updated_at"])

        response = self.client.get("/empresas/", HTTP_HOST="candidomecanicaautomotriz.incardbook.test")

        self.assertNotEqual(response.request["PATH_INFO"], "/site/candidomecanicaautomotriz/empresas/")

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

    def test_dashboard_builder_can_delete_non_home_page(self):
        owner = make_user("deletepageowner")
        company = make_company(owner=owner, name="Delete Page Company")
        website = create_starter_website(company, publish=True)
        page = Page.objects.create(website=website, title="No deseada", slug="no-deseada", is_published=True)
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {"action": "delete_page", "page_id": page.id},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Page.objects.filter(pk=page.pk).exists())

    def test_dashboard_builder_can_delete_home_page_and_assign_replacement(self):
        owner = make_user("deletehomeowner")
        company = make_company(owner=owner, name="Delete Home Company")
        website = create_starter_website(company, publish=True)
        home_page = website.pages.get(is_homepage=True)
        replacement = Page.objects.create(website=website, title="Servicios", slug="servicios", order=2, is_published=True)
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {"action": "delete_page", "page_id": home_page.id},
        )

        replacement.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Page.objects.filter(pk=home_page.pk).exists())
        self.assertTrue(replacement.is_homepage)
        self.assertTrue(replacement.is_published)
        self.assertTrue(replacement.show_in_menu)

    def test_dashboard_builder_cannot_delete_only_active_page(self):
        owner = make_user("deleteonlypageowner")
        company = make_company(owner=owner, name="Delete Only Page Company")
        website = create_starter_website(company, publish=True)
        only_page = website.pages.get(is_homepage=True)
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {"action": "delete_page", "page_id": only_page.id},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Page.objects.filter(pk=only_page.pk).exists())

    def test_dashboard_builder_saves_service_component_icon(self):
        owner = make_user("serviceiconowner")
        company = make_company(owner=owner, name="Service Icon Company")
        website = create_starter_website(company, publish=True)
        section = website.pages.get(is_homepage=True).layout.sections.get(section_type="services")
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {
                "action": "create_component",
                "section_id": section.id,
                "component_type": "service_card",
                "name": "Mecanica general",
                "title": "Mecanica general",
                "subtitle": "Servicio automotriz",
                "service_icon": "car",
                "order": 8,
                "is_active": "on",
            },
        )

        component = Component.objects.get(section=section, title="Mecanica general")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(component.settings["icon"], "car")

    def test_public_services_render_flip_cards_with_svg_icons(self):
        company = make_company(owner=make_user("serviceflipowner"), name="Service Flip Company")
        website = create_starter_website(company, publish=True)
        section = website.pages.get(is_homepage=True).layout.sections.get(section_type="services")
        component = section.components.filter(component_type="service_card").first()
        component.settings = {"icon": "wrench"}
        component.save(update_fields=["settings", "updated_at"])

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "wb-service-flip-card")
        self.assertContains(response, "<svg viewBox=")

    def test_dashboard_builder_updates_public_contact_visibility(self):
        owner = make_user("visibilityowner")
        company = make_company(owner=owner, name="Visibility Company")
        create_starter_website(company, publish=True)
        self.client.force_login(owner)

        response = self.client.post(
            reverse("dashboard-company-website", kwargs={"company_id": company.id}),
            {
                "action": "update_contact_visibility",
                "show_email": "on",
                "show_website": "on",
            },
        )

        company.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(company.show_phone)
        self.assertFalse(company.show_whatsapp)
        self.assertTrue(company.show_email)
        self.assertTrue(company.show_website)
        self.assertFalse(company.show_address)

    def test_public_site_hides_contact_blocks_by_company_visibility(self):
        company = make_company(
            owner=make_user("hiddencontactowner"),
            name="Hidden Contact Company",
            phone_number="+18095550100",
            email="visible@example.com",
            address="123 Hidden Street",
            show_phone=False,
            show_address=False,
            show_email=True,
        )
        website = create_starter_website(company, publish=True)
        footer = website.pages.get(is_homepage=True).layout.sections.get(section_type="footer")
        component = footer.components.filter(component_type="contact_info").first()
        Block.objects.create(component=component, block_type="phone", key="phone", value=company.phone_number, order=10)
        Block.objects.create(component=component, block_type="email", key="email", value=company.email, order=11)
        Block.objects.create(component=component, block_type="address", key="address", value=company.address, order=12)

        response = self.client.get(reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "+18095550100")
        self.assertNotContains(response, "123 Hidden Street")
        self.assertContains(response, "visible@example.com")
