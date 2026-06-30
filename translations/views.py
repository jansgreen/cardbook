from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response
from cards.models import DigitalCard
from cards.permissions import can_manage_card
from .models import CardTranslation
from .serializers import CardTranslationSerializer


class CardTranslationListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_card(self, card_id):
        try:
            return DigitalCard.objects.get(id=card_id, is_active=True)
        except DigitalCard.DoesNotExist:
            return None

    def get(self, request, card_id):
        card = self.get_card(card_id)
        if not card:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        translations = CardTranslation.objects.filter(card=card)
        return success_response("Translations retrieved successfully.", CardTranslationSerializer(translations, many=True).data)

    def post(self, request, card_id):
        card = self.get_card(card_id)
        if not card:
            return error_response("Card not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_card(request.user, card):
            return error_response("You do not have permission to edit translations.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = CardTranslationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Translation creation failed.", serializer.errors)
        translation = serializer.save(card=card)
        return success_response("Translation created successfully.", CardTranslationSerializer(translation).data, status.HTTP_201_CREATED)
