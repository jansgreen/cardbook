from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from cardbookweb.responses import error_response, success_response
from .serializers import ProfileSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Registration failed.", serializer.errors)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success_response(
            "User registered successfully.",
            {
                "user": ProfileSerializer(user, context={"request": request}).data,
                "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
            },
            status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid credentials.", serializer.errors, status.HTTP_401_UNAUTHORIZED)
        user = serializer.user
        tokens = serializer.validated_data
        return success_response(
            "Login successful.",
            {
                "user": ProfileSerializer(user, context={"request": request}).data,
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
        )


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response("Refresh token is required.", {"refresh": ["This field is required."]})

        try:
            RefreshToken(refresh_token).blacklist()
        except Exception as exc:
            return error_response("Logout failed.", {"refresh": [str(exc)]})

        return success_response("Logout successful.")


class ProfileView(APIView):
    def get(self, request):
        return success_response(
            "Profile retrieved successfully.",
            ProfileSerializer(request.user, context={"request": request}).data,
        )

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Profile update failed.", serializer.errors)
        serializer.save()
        return success_response("Profile updated successfully.", serializer.data)
