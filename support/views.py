from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response

from .models import SupportTicket
from .serializers import SupportTicketSerializer


class SupportTicketListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user)[:20]
        serializer = SupportTicketSerializer(tickets, many=True, context={"request": request})
        return success_response("Support tickets retrieved successfully.", serializer.data)

    def post(self, request):
        serializer = SupportTicketSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Support ticket creation failed.", serializer.errors)
        ticket = serializer.save()
        return success_response(
            "Support ticket created successfully.",
            SupportTicketSerializer(ticket, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )
