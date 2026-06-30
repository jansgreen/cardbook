from django.db.models import Count
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response
from companies.models import Company
from .models import CompanyRating


class CompanyRatingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, company_id):
        company = Company.objects.filter(pk=company_id, is_active=True).first()
        if not company:
            return error_response("Company not found.", status_code=status.HTTP_404_NOT_FOUND)
        efficient, created = CompanyRating.objects.get_or_create(
            company=company,
            user=request.user,
            defaults={"stars": 1},
        )
        stats = CompanyRating.objects.filter(company=company).aggregate(total=Count("id"))
        return success_response(
            "Company efficient star saved." if created else "Company already marked as efficient.",
            {
                "id": efficient.id,
                "efficient": created,
                "total": stats["total"],
            },
        )
