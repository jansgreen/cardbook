from rest_framework import status
from rest_framework.test import APITestCase

from accesscontrol.models import AccessRole, UserAccessGrant
from accesscontrol.services import ensure_default_permissions
from cardbookweb.test_utils import make_company, make_user
from cards.services import can_create_profile_for_company, profile_creation_companies


class AgentCardPermissionTests(APITestCase):
    def test_agent_can_create_digital_profile_under_assigned_company(self):
        ensure_default_permissions()
        owner = make_user("cardbookowner")
        agent = make_user("agentuser")
        company = make_company(owner=owner, name="Cardbook")
        role = AccessRole.objects.get(name="Agente Cardbook")
        UserAccessGrant.objects.create(user=agent, company=company, role=role, commission_percent="15.00")

        self.client.force_authenticate(agent)
        response = self.client.post(
            "/api/v1/cards/",
            {
                "company": company.id,
                "job_title": "Agente",
                "email": "agent@cardbook.test",
            },
            format="json",
            HTTP_HOST="127.0.0.1:8000",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(can_create_profile_for_company(agent, company))
        self.assertIn(company.id, list(profile_creation_companies(agent).values_list("id", flat=True)))

    def test_agent_cannot_create_profile_under_unassigned_company(self):
        ensure_default_permissions()
        owner = make_user("owner2")
        agent = make_user("agent2")
        assigned_company = make_company(owner=owner, name="Cardbook")
        other_company = make_company(owner=owner, name="Other Co")
        role = AccessRole.objects.get(name="Agente Cardbook")
        UserAccessGrant.objects.create(user=agent, company=assigned_company, role=role)

        self.client.force_authenticate(agent)
        response = self.client.post(
            "/api/v1/cards/",
            {
                "company": other_company.id,
                "job_title": "Agente",
            },
            format="json",
            HTTP_HOST="127.0.0.1:8000",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(can_create_profile_for_company(agent, other_company))
