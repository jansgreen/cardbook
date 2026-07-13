from rest_framework import serializers

from .models import PushDevice


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = ["id", "token", "platform", "device_id", "app_version", "enabled", "last_seen_at", "created_at"]
        read_only_fields = ["id", "last_seen_at", "created_at"]

    def validate_token(self, value):
        value = value.strip()
        if len(value) < 20:
            raise serializers.ValidationError("Token invalido.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        token = validated_data.pop("token")
        device, _ = PushDevice.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "enabled": True,
                **validated_data,
            },
        )
        return device
