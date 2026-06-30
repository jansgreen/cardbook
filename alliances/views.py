from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import StandardPagination, error_response, success_response
from companies.models import Company
from companies.permissions import can_manage_company
from .models import CompanyAlliance
from .serializers import CompanyAllianceSerializer


class AllianceListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company_ids = Company.objects.filter(is_active=True, owner=request.user).values_list("id", flat=True)
        alliances = CompanyAlliance.objects.filter(requester_id__in=company_ids) | CompanyAlliance.objects.filter(receiver_id__in=company_ids)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(alliances.distinct().select_related("requester", "receiver", "requested_by"), request)
        return paginator.get_paginated_response(CompanyAllianceSerializer(page, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = CompanyAllianceSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Alliance request failed.", serializer.errors)
        requester = serializer.validated_data["requester"]
        receiver = serializer.validated_data["receiver"]
        if requester == receiver:
            return error_response("A company cannot ally with itself.")
        if not can_manage_company(request.user, requester):
            return error_response("You do not have permission to request alliances for this company.", status_code=status.HTTP_403_FORBIDDEN)
        alliance, created = CompanyAlliance.objects.get_or_create(
            requester=requester,
            receiver=receiver,
            defaults={"requested_by": request.user},
        )
        return success_response(
            "Alliance request created." if created else "Alliance request already exists.",
            CompanyAllianceSerializer(alliance, context={"request": request}).data,
            status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AllianceDecisionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, decision):
        alliance = CompanyAlliance.objects.filter(pk=pk).select_related("requester", "receiver").first()
        if not alliance:
            return error_response("Alliance not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, alliance.receiver):
            return error_response("Only the receiving company can decide this alliance.", status_code=status.HTTP_403_FORBIDDEN)
        if decision not in {CompanyAlliance.STATUS_ACCEPTED, CompanyAlliance.STATUS_REJECTED}:
            return error_response("Invalid alliance decision.")
        alliance.status = decision
        alliance.save(update_fields=["status", "updated_at"])
        return success_response("Alliance updated.", CompanyAllianceSerializer(alliance, context={"request": request}).data)
