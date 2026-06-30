from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response
from companies.models import Company
from companies.permissions import can_access_company, can_manage_company
from .models import CompanyMember
from .serializers import CompanyMemberSerializer


def is_company_owner(user, company):
    return user.is_authenticated and company.owner_id == user.id


class CompanyMemberListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_company(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            return None
        return company if can_access_company(request.user, company) else None

    def get(self, request, company_id):
        company = self.get_company(request, company_id)
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        members = CompanyMember.objects.filter(company=company, is_active=True).select_related("user")
        return success_response("Members retrieved successfully.", CompanyMemberSerializer(members, many=True).data)

    def post(self, request, company_id):
        company = self.get_company(request, company_id)
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, company):
            return error_response("You do not have permission to add members.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = CompanyMemberSerializer(data=request.data, context={"request": request, "company": company})
        if not serializer.is_valid():
            return error_response("Member creation failed.", serializer.errors)
        member = serializer.save(company=company)
        return success_response("Member created successfully.", CompanyMemberSerializer(member).data, status.HTTP_201_CREATED)


class CompanyMemberDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_member(self, request, company_id, member_id):
        try:
            member = CompanyMember.objects.select_related("company").get(id=member_id, company_id=company_id, is_active=True)
        except CompanyMember.DoesNotExist:
            return None
        return member if can_access_company(request.user, member.company) else None

    def patch(self, request, company_id, member_id):
        member = self.get_member(request, company_id, member_id)
        if not member:
            return error_response("Member not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, member.company):
            return error_response("You do not have permission to edit members.", status_code=status.HTTP_403_FORBIDDEN)
        if member.role == CompanyMember.ROLE_OWNER and not is_company_owner(request.user, member.company):
            return error_response("Only the company owner can edit an owner membership.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = CompanyMemberSerializer(member, data=request.data, partial=True, context={"request": request, "company": member.company})
        if not serializer.is_valid():
            return error_response("Member update failed.", serializer.errors)
        serializer.save()
        return success_response("Member updated successfully.", serializer.data)

    def delete(self, request, company_id, member_id):
        member = self.get_member(request, company_id, member_id)
        if not member:
            return error_response("Member not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, member.company):
            return error_response("You do not have permission to delete members.", status_code=status.HTTP_403_FORBIDDEN)
        if member.role == CompanyMember.ROLE_OWNER:
            return error_response("Owner membership cannot be deleted.", status_code=status.HTTP_403_FORBIDDEN)
        member.is_active = False
        member.save(update_fields=["is_active"])
        return success_response("Member deleted successfully.")
