from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


Profile = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "preferred_language",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "username", "created_at", "updated_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "preferred_language",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        password_confirm = attrs.pop("password_confirm")
        if attrs["password"] != password_confirm:
            raise serializers.ValidationError({"password_confirm": ["Passwords do not match."]})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Profile(**validated_data)
        user.set_password(password)
        user.save()
        return user
