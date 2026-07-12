from rest_framework.test import APITestCase

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import ensure_default_permissions
from cardbookweb.test_utils import make_company, make_user
from websitebuilder.models import Page, Website
from websitebuilder.services import can_manage_website_builder, can_publish_website_builder, create_starter_website, website_publish_status


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
