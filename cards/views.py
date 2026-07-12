from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import StandardPagination, error_response, success_response
from .models import BusinessCard, DigitalCard
from .serializers import BusinessCardSerializer, DigitalCardSerializer, PublicDigitalCardSerializer
from .services import (
    can_manage_business_profile,
    can_use_profile_for_business_card,
    visible_business_cards_queryset,
    visible_profiles_queryset,
)


class CardListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cards = visible_profiles_queryset(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(cards, request)
        serializer = DigitalCardSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = DigitalCardSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Card creation failed.", serializer.errors)
        card = serializer.save(user=request.user)
        return success_response(
            "Card created successfully.",
            DigitalCardSerializer(card, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class BusinessCardListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cards = visible_business_cards_queryset(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(cards, request)
        serializer = BusinessCardSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BusinessCardSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Business card creation failed.", serializer.errors)
        card = serializer.save()
        return success_response(
            "Business card created successfully.",
            BusinessCardSerializer(card, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class PublicCardDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            card = DigitalCard.objects.select_related("company", "user").get(slug=slug, is_active=True)
        except DigitalCard.DoesNotExist:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = PublicDigitalCardSerializer(
            card,
            context={"request": request, "language": request.query_params.get("lang", "es")},
        )
        return success_response("Card retrieved successfully.", serializer.data)


class CardDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_card(self, pk):
        try:
            return DigitalCard.objects.select_related("company", "user").get(pk=pk, is_active=True)
        except DigitalCard.DoesNotExist:
            return None

    def patch(self, request, pk):
        card = self.get_card(pk)
        if not card:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_business_profile(request.user, card):
            return error_response("You do not have permission to edit this card.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = DigitalCardSerializer(card, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Card update failed.", serializer.errors)
        serializer.save()
        return success_response("Card updated successfully.", serializer.data)

    def delete(self, request, pk):
        card = self.get_card(pk)
        if not card:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_business_profile(request.user, card):
            return error_response("You do not have permission to delete this card.", status_code=status.HTTP_403_FORBIDDEN)
        card.is_active = False
        card.save(update_fields=["is_active", "updated_at"])
        return success_response("Card deleted successfully.")


class BusinessCardDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_card(self, pk):
        try:
            return BusinessCard.objects.select_related("profile", "profile__company", "profile__user").get(
                pk=pk,
                is_active=True,
            )
        except BusinessCard.DoesNotExist:
            return None

    def patch(self, request, pk):
        card = self.get_card(pk)
        if not card:
            return error_response("Business card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_use_profile_for_business_card(request.user, card.profile):
            return error_response("You do not have permission to edit this business card.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = BusinessCardSerializer(card, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Business card update failed.", serializer.errors)
        serializer.save()
        return success_response("Business card updated successfully.", serializer.data)

    def delete(self, request, pk):
        card = self.get_card(pk)
        if not card:
            return error_response("Business card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_use_profile_for_business_card(request.user, card.profile):
            return error_response("You do not have permission to delete this business card.", status_code=status.HTTP_403_FORBIDDEN)
        card.is_active = False
        card.save(update_fields=["is_active", "updated_at"])
        return success_response("Business card deleted successfully.")
