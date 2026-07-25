from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accesscontrol.models import AccessPermission, AccessRole, UserAccessGrant
from accesscontrol.permissions import user_can_manage_access_catalog
from accesscontrol.services import PERM_MANAGE_ACCESS_CONTROL, PERM_MANAGE_AI_AGENTS, ensure_default_permissions
from companies.models import Company


class AccessControlPermissionsTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.owner = self.User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass12345",
        )
        self.user = self.User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="pass12345",
        )
        self.access_manager = self.User.objects.create_user(
            username="access_manager",
            email="access@example.com",
            password="pass12345",
        )
        self.superuser = self.User.objects.create_user(
            username="superaccess",
            email="superaccess@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.company = Company.objects.create(owner=self.owner, name="Jans Green", is_active=True)
        ensure_default_permissions()

    def test_default_permissions_include_ai_agent_manager_role(self):
        permission = AccessPermission.objects.get(code=PERM_MANAGE_AI_AGENTS)
        role = AccessRole.objects.get(name="Administrador de agentes IA")

        self.assertTrue(role.permissions.filter(pk=permission.pk).exists())

    def test_regular_user_cannot_open_access_control(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard-access-control"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-home"))

    def test_company_owner_cannot_open_access_control(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("dashboard-access-control"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-home"))
        self.assertFalse(user_can_manage_access_catalog(self.owner, self.company))

    def test_company_owner_cannot_create_global_permission(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("dashboard-access-control"),
            {
                "action": "create_permission",
                "company": self.company.id,
                "code": "test.owner_denied",
                "name": "Owner denied",
                "description": "No debe crearse",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(AccessPermission.objects.filter(code="test.owner_denied").exists())

    def test_superuser_can_create_global_permission(self):
        permission = AccessPermission.objects.get(code=PERM_MANAGE_ACCESS_CONTROL)
        role = AccessRole.objects.create(name="Administrador de accesos")
        role.permissions.add(permission)
        UserAccessGrant.objects.create(
            user=self.access_manager,
            company=self.company,
            role=role,
            is_active=True,
        )
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("dashboard-access-control"),
            {
                "action": "create_permission",
                "company": self.company.id,
                "code": "test.catalog_allowed",
                "name": "Catalog allowed",
                "description": "Permiso creado desde prueba",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(AccessPermission.objects.filter(code="test.catalog_allowed").exists())
        self.assertTrue(user_can_manage_access_catalog(self.superuser, self.company))
