import json
import urllib.error
import urllib.request

from django.conf import settings

from .models import PushDeliveryLog, PushDevice


FCM_LEGACY_URL = "https://fcm.googleapis.com/fcm/send"


def fcm_is_configured():
    return bool(getattr(settings, "FCM_SERVER_KEY", ""))


def register_push_device(*, user, token, platform="android", device_id="", app_version=""):
    device, _ = PushDevice.objects.update_or_create(
        token=token,
        defaults={
            "user": user,
            "platform": platform,
            "device_id": device_id,
            "app_version": app_version,
            "enabled": True,
        },
    )
    return device


def disable_push_device(*, user, token):
    return PushDevice.objects.filter(user=user, token=token).update(enabled=False)


def send_push_to_user(*, user, title, body="", data=None):
    devices = PushDevice.objects.filter(user=user, enabled=True)
    logs = []
    for device in devices:
        logs.append(send_push_to_device(device=device, title=title, body=body, data=data or {}))
    return logs


def send_push_to_device(*, device, title, body="", data=None):
    payload = {
        "to": device.token,
        "notification": {"title": title, "body": body},
        "data": {key: str(value) for key, value in (data or {}).items()},
        "priority": "high",
    }
    log = PushDeliveryLog.objects.create(
        user=device.user,
        device=device,
        title=title,
        body=body,
        data=data or {},
        status=PushDeliveryLog.STATUS_PENDING,
    )

    server_key = getattr(settings, "FCM_SERVER_KEY", "")
    if not server_key:
        log.status = PushDeliveryLog.STATUS_SKIPPED
        log.provider_response = "FCM_SERVER_KEY is not configured."
        log.save(update_fields=["status", "provider_response"])
        return log

    request = urllib.request.Request(
        FCM_LEGACY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"key={server_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            log.status = PushDeliveryLog.STATUS_SENT if response.status < 400 else PushDeliveryLog.STATUS_FAILED
            log.provider_response = response_body[:2000]
    except urllib.error.URLError as exc:
        log.status = PushDeliveryLog.STATUS_FAILED
        log.provider_response = str(exc)[:2000]

    log.save(update_fields=["status", "provider_response"])
    return log
