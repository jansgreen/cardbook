from django.db.models import Avg, Count, Q
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import StandardPagination, error_response, success_response
from company_ratings.views import CompanyRatingView
from memberships.models import CompanyMember
from .models import Company
from .permissions import can_access_company, can_manage_company
from .serializers import CompanySerializer


class CompanyListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = (
            Company.objects.filter(is_active=True, owner=request.user)
            | Company.objects.filter(is_active=True, members__user=request.user, members__is_active=True)
        ).distinct()
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CompanySerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Company creation failed.", serializer.errors)
        company = serializer.save(owner=request.user)
        CompanyMember.objects.create(company=company, user=request.user, role=CompanyMember.ROLE_OWNER)
        return success_response(
            "Company created successfully.",
            CompanySerializer(company, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class CompanyDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        try:
            company = Company.objects.get(pk=pk, is_active=True)
        except Company.DoesNotExist:
            return None
        if not can_access_company(request.user, company):
            return None
        return company

    def get(self, request, pk):
        company = self.get_object(request, pk)
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("Company retrieved successfully.", CompanySerializer(company, context={"request": request}).data)

    def patch(self, request, pk):
        company = self.get_object(request, pk)
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, company):
            return error_response("You do not have permission to edit this company.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = CompanySerializer(company, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Company update failed.", serializer.errors)
        serializer.save()
        return success_response("Company updated successfully.", serializer.data)

    def delete(self, request, pk):
        company = self.get_object(request, pk)
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, company):
            return error_response("You do not have permission to delete this company.", status_code=status.HTTP_403_FORBIDDEN)
        company.is_active = False
        company.save(update_fields=["is_active", "updated_at"])
        return success_response("Company deleted successfully.")


class CompanyRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        base_id = request.query_params.get("company")
        base_company = None
        if base_id:
            base_company = Company.objects.filter(pk=base_id, is_active=True).first()
            if base_company and not can_access_company(request.user, base_company):
                return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)

        queryset = Company.objects.filter(is_active=True).exclude(owner=request.user)
        if base_company:
            filters = Q()
            if base_company.category:
                filters |= Q(category__iexact=base_company.category)
            if base_company.city:
                filters |= Q(city__iexact=base_company.city)
            if base_company.region:
                filters |= Q(region__iexact=base_company.region)
            if base_company.services:
                for term in [part.strip() for part in base_company.services.replace("\n", ",").split(",") if part.strip()][:4]:
                    filters |= Q(services__icontains=term)
            if filters:
                queryset = queryset.filter(filters)
            queryset = queryset.exclude(pk=base_company.pk)

        queryset = queryset.annotate(
            efficient_total=Count("ratings", distinct=True),
            rating_total=Count("ratings", distinct=True),
        ).order_by("-efficient_total", "name")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CompanySerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
