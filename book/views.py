from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import StandardPagination, error_response, success_response
from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from .models import SavedBusiness
from .serializers import SavedBusinessSerializer


def resolve_saved_business_payload(user, data):
    company = None
    digital_card = None
    business_card = None

    if data.get("digital_card"):
        digital_card = get_object_or_404(DigitalCard.objects.filter(is_active=True), pk=data["digital_card"])
        company = digital_card.company
    if data.get("business_card"):
        business_card = get_object_or_404(BusinessCard.objects.filter(is_active=True), pk=data["business_card"])
        company = business_card.company
        digital_card = digital_card or business_card.profile
    if data.get("company"):
        company = get_object_or_404(Company.objects.filter(is_active=True), pk=data["company"])

    if not company:
        return None, None, None, "Company, digital_card or business_card is required."
    if company.owner_id == user.id:
        return None, None, None, "You cannot save your own company in Book."
    return company, digital_card, business_card, None


class SavedBusinessListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = SavedBusiness.objects.filter(user=request.user).select_related(
            "company",
            "digital_card__company",
            "digital_card__user",
            "business_card__profile__company",
            "business_card__profile__user",
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = SavedBusinessSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        company, digital_card, business_card, error = resolve_saved_business_payload(request.user, request.data)
        if error:
            return error_response(error, status_code=status.HTTP_400_BAD_REQUEST)
        item, created = SavedBusiness.objects.get_or_create(
            user=request.user,
            company=company,
            defaults={
                "digital_card": digital_card,
                "business_card": business_card,
                "notes": request.data.get("notes") or "",
            },
        )
        changed = False
        if digital_card and not item.digital_card_id:
            item.digital_card = digital_card
            changed = True
        if business_card and not item.business_card_id:
            item.business_card = business_card
            changed = True
        if request.data.get("notes") is not None:
            item.notes = request.data.get("notes")
            changed = True
        if changed:
            item.save()
        return success_response(
            "Saved in Book." if created else "Already saved in Book.",
            SavedBusinessSerializer(item, context={"request": request}).data,
            status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SavedBusinessDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        item = SavedBusiness.objects.filter(pk=pk, user=request.user).first()
        if not item:
            return error_response("Book item not found.", status_code=status.HTTP_404_NOT_FOUND)
        item.delete()
        return success_response("Removed from Book.")
