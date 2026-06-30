from django.db.models import Count
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response
from cards.models import DigitalCard
from cards.permissions import can_manage_card
from .models import CardClick, CardView
from .serializers import CardClickSerializer, CardViewSerializer


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class CardViewCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, card_id):
        try:
            card = DigitalCard.objects.get(id=card_id, is_active=True)
        except DigitalCard.DoesNotExist:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = CardViewSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Card view registration failed.", serializer.errors)
        view = serializer.save(
            card=card,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return success_response("Card view registered.", CardViewSerializer(view).data, status.HTTP_201_CREATED)


class CardClickCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, card_id):
        try:
            card = DigitalCard.objects.get(id=card_id, is_active=True)
        except DigitalCard.DoesNotExist:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = CardClickSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Card click registration failed.", serializer.errors)
        click = serializer.save(card=card)
        return success_response("Card click registered.", CardClickSerializer(click).data, status.HTTP_201_CREATED)


class CardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, card_id):
        try:
            card = DigitalCard.objects.get(id=card_id, is_active=True)
        except DigitalCard.DoesNotExist:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_card(request.user, card):
            return error_response("You do not have permission to view these stats.", status_code=status.HTTP_403_FORBIDDEN)

        data = {
            "card_id": card.id,
            "views": CardView.objects.filter(card=card).count(),
            "clicks": CardClick.objects.filter(card=card).count(),
            "clicks_by_type": list(CardClick.objects.filter(card=card).values("click_type").annotate(total=Count("id"))),
        }
        return success_response("Card stats retrieved successfully.", data)
