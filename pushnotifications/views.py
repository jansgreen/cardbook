from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import error_response, success_response

from .models import PushDevice
from .serializers import PushDeviceSerializer
from .services import disable_push_device, fcm_is_configured, send_push_to_user


class PushDeviceListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        devices = PushDevice.objects.filter(user=request.user)
        serializer = PushDeviceSerializer(devices, many=True, context={"request": request})
        return success_response(
            "Push devices retrieved successfully.",
            {
                "fcm_configured": fcm_is_configured(),
                "results": serializer.data,
            },
        )

    def post(self, request):
        serializer = PushDeviceSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Push device registration failed.", serializer.errors)
        device = serializer.save()
        return success_response(
            "Push device registered successfully.",
            PushDeviceSerializer(device, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class PushDeviceDisableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("token", "").strip()
        if not token:
            return error_response("Token is required.", {"token": ["This field is required."]})
        updated = disable_push_device(user=request.user, token=token)
        return success_response("Push device disabled successfully.", {"updated": updated})


class PushTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logs = send_push_to_user(
            user=request.user,
            title="Cardbook",
            body="Notificacion de prueba enviada desde Cardbook.",
            data={"event_type": "test", "route": "/notifications"},
        )
        return success_response(
            "Push test processed successfully.",
            {
                "fcm_configured": fcm_is_configured(),
                "deliveries": [
                    {"id": log.id, "status": log.status, "response": log.provider_response}
                    for log in logs
                ],
            },
        )
