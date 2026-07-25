from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from memberships.models import CompanyMember
from referrals.models import AgentApplication, AgentProfile, Referral


class AndroidApiFlowTests(APITestCase):
    def register_user(self, username="demo", email="demo@example.com"):
        response = self.client.post(
            reverse("register"),
            {
                "username": username,
                "email": email,
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "preferred_language": "es",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        return response.data["data"]

    def authenticate(self, username="demo", email="demo@example.com"):
        data = self.register_user(username=username, email=email)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['tokens']['access']}")
        return data

    def create_company(self, name="Cardbook Coffee"):
        response = self.client.post(
            "/api/v1/companies/",
            {
                "name": name,
                "phone_number": "+18095550100",
                "email": "hello@cardbook.test",
                "website": "https://cardbook.test",
                "description": "Digital cards for local businesses.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["data"]

    def create_card(self, company_id):
        response = self.client.post(
            "/api/v1/cards/",
            {
                "company": company_id,
                "job_title": "Founder",
                "phone_number": "+18095550100",
                "email": "demo@cardbook.test",
                "website": "https://cardbook.test/demo",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["data"]

    def test_register_returns_tokens(self):
        data = self.register_user()
        self.assertIn("access", data["tokens"])
        self.assertIn("refresh", data["tokens"])

    def test_register_saves_registration_intent(self):
        data = self.register_user(username="jobintent", email="jobintent@example.com")
        user = get_user_model().objects.get(id=data["user"]["id"])
        self.assertEqual(user.registration_intent, "")

        response = self.client.post(
            reverse("register"),
            {
                "username": "mobilejob",
                "email": "mobilejob@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "preferred_language": "es",
                "registration_intent": "job",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(username="mobilejob")
        self.assertEqual(user.registration_intent, "job")

    def test_register_rejects_invalid_agent_referral_code(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "badagent",
                "email": "badagent@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "registration_intent": "agent",
                "referral_code": "AGT-NOPE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.filter(username="badagent").exists())

    def test_register_agent_with_valid_referral_code_creates_referral(self):
        agent = get_user_model().objects.create_user(
            username="agentowner",
            email="agentowner@example.com",
            password="StrongPassword123!",
        )
        AgentProfile.objects.create(user=agent, referral_code="AGT-MOBILE")

        response = self.client.post(
            reverse("register"),
            {
                "username": "goodagent",
                "email": "goodagent@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "registration_intent": "agent",
                "referral_code": "AGT-MOBILE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(username="goodagent")
        self.assertEqual(user.registration_intent, "agent")
        self.assertTrue(Referral.objects.filter(referred_user=user, referral_code="AGT-MOBILE").exists())

    def test_agent_application_api_creates_pending_application(self):
        response = self.client.post(
            "/api/v1/referrals/agent/apply/",
            {
                "full_name": "Ana Mobile",
                "email": "ana.mobile@example.com",
                "phone_number": "+18095550123",
                "city": "Santo Domingo",
                "experience": "Ventas y tecnologia.",
                "reason": "Quiero representar Cardbook con empresas locales.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AgentApplication.objects.filter(email="ana.mobile@example.com").exists())

    def test_android_end_to_end_flow(self):
        self.authenticate()

        profile_response = self.client.get("/api/v1/accounts/profile/")
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["data"]["username"], "demo")

        company = self.create_company()
        card = self.create_card(company["id"])

        translation_response = self.client.post(
            f"/api/v1/cards/{card['id']}/translations/",
            {
                "language": "es",
                "full_name": "Demo User",
                "bio": "Especialista en tarjetas digitales.",
                "services": "Diseño, QR, perfiles digitales",
                "address": "Santo Domingo",
                "custom_message": "Conecta conmigo.",
            },
            format="json",
        )
        self.assertEqual(translation_response.status_code, status.HTTP_201_CREATED)

        public_response = self.client.get(f"/api/v1/cards/{card['slug']}/?lang=en")
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        self.assertEqual(public_response.data["data"]["translation"]["language"], "es")

        view_response = self.client.post(
            f"/api/v1/analytics/cards/{card['id']}/view/",
            {"source": "qr", "language": "es"},
            format="json",
        )
        self.assertEqual(view_response.status_code, status.HTTP_201_CREATED)

        click_response = self.client.post(
            f"/api/v1/analytics/cards/{card['id']}/click/",
            {"click_type": "website"},
            format="json",
        )
        self.assertEqual(click_response.status_code, status.HTTP_201_CREATED)

        stats_response = self.client.get(f"/api/v1/analytics/cards/{card['id']}/stats/")
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertEqual(stats_response.data["data"]["views"], 1)
        self.assertEqual(stats_response.data["data"]["clicks"], 1)


class PermissionSecurityTests(APITestCase):
    password = "StrongPassword123!"

    def create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@cardbook.test",
            password=self.password,
        )

    def auth_as(self, user):
        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access']}")

    def create_company_as_owner(self, owner):
        self.auth_as(owner)
        response = self.client.post("/api/v1/companies/", {"name": "Secure Co"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["data"]

    def add_member(self, company_id, user, role):
        response = self.client.post(
            f"/api/v1/companies/{company_id}/members/",
            {"user": user.id, "role": role},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["data"]

    def test_staff_cannot_edit_company(self):
        owner = self.create_user("owner")
        staff = self.create_user("staff")
        company = self.create_company_as_owner(owner)
        self.add_member(company["id"], staff, CompanyMember.ROLE_STAFF)

        self.auth_as(staff)
        response = self.client.patch(f"/api/v1/companies/{company['id']}/", {"name": "Nope"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])

    def test_outside_user_cannot_read_company(self):
        owner = self.create_user("owner")
        outsider = self.create_user("outsider")
        company = self.create_company_as_owner(owner)

        self.auth_as(outsider)
        response = self.client.get(f"/api/v1/companies/{company['id']}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_cannot_assign_owner_role(self):
        owner = self.create_user("owner")
        admin = self.create_user("admin")
        staff = self.create_user("staff")
        company = self.create_company_as_owner(owner)
        self.add_member(company["id"], admin, CompanyMember.ROLE_ADMIN)

        self.auth_as(admin)
        response = self.client.post(
            f"/api/v1/companies/{company['id']}/members/",
            {"user": staff.id, "role": CompanyMember.ROLE_OWNER},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_admin_cannot_edit_or_delete_owner_membership(self):
        owner = self.create_user("owner")
        admin = self.create_user("admin")
        company = self.create_company_as_owner(owner)
        self.add_member(company["id"], admin, CompanyMember.ROLE_ADMIN)
        owner_membership = CompanyMember.objects.get(company_id=company["id"], user=owner)

        self.auth_as(admin)
        patch_response = self.client.patch(
            f"/api/v1/companies/{company['id']}/members/{owner_membership.id}/",
            {"role": CompanyMember.ROLE_STAFF},
            format="json",
        )
        delete_response = self.client.delete(f"/api/v1/companies/{company['id']}/members/{owner_membership.id}/")

        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_edit_own_card_but_not_another_staff_card(self):
        owner = self.create_user("owner")
        staff = self.create_user("staff")
        other_staff = self.create_user("otherstaff")
        company = self.create_company_as_owner(owner)
        self.add_member(company["id"], staff, CompanyMember.ROLE_STAFF)
        self.add_member(company["id"], other_staff, CompanyMember.ROLE_STAFF)

        self.auth_as(staff)
        own_card = self.client.post(
            "/api/v1/cards/",
            {"company": company["id"], "job_title": "Staff"},
            format="json",
        ).data["data"]

        self.auth_as(other_staff)
        forbidden = self.client.patch(
            f"/api/v1/cards/{own_card['id']}/",
            {"job_title": "Hijacked"},
            format="json",
        )

        self.auth_as(staff)
        allowed = self.client.patch(
            f"/api/v1/cards/{own_card['id']}/",
            {"job_title": "Updated"},
            format="json",
        )

        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
