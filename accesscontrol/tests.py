from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accesscontrol.models import AccessPermission, AccessRole, UserAccessGrant
from accesscontrol.permissions import user_can_manage_access_catalog
from accesscontrol.services import PERM_MANAGE_ACCESS_CONTROL, ensure_default_permissions
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
        self.company = Company.objects.create(owner=self.owner, name="Jans Green", is_active=True)
        ensure_default_permissions()

    def test_regular_user_cannot_open_access_control(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard-access-control"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-home"))

    def test_company_owner_can_open_access_control_but_not_catalog(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("dashboard-access-control"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Miembros activos")
        self.assertContains(response, "Modo lectura")
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

    def test_access_manage_grant_can_create_global_permission(self):
        permission = AccessPermission.objects.get(code=PERM_MANAGE_ACCESS_CONTROL)
        role = AccessRole.objects.create(name="Administrador de accesos")
        role.permissions.add(permission)
        UserAccessGrant.objects.create(
            user=self.access_manager,
            company=self.company,
            role=role,
            is_active=True,
        )
        self.client.force_login(self.access_manager)

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
        self.assertTrue(user_can_manage_access_catalog(self.access_manager, self.company))
