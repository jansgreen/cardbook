import hashlib
import re

from django.conf import settings
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


ASK_LIMIT = getattr(settings, "AI_AGENT_PUBLIC_ASK_LIMIT", 30)
ASK_WINDOW_SECONDS = getattr(settings, "AI_AGENT_PUBLIC_ASK_WINDOW_SECONDS", 60)
LEAD_LIMIT = getattr(settings, "AI_AGENT_PUBLIC_LEAD_LIMIT", 5)
LEAD_WINDOW_SECONDS = getattr(settings, "AI_AGENT_PUBLIC_LEAD_WINDOW_SECONDS", 60 * 60)
MAX_QUESTION_LENGTH = getattr(settings, "AI_AGENT_MAX_QUESTION_LENGTH", 500)
MAX_LEAD_FIELD_LENGTH = getattr(settings, "AI_AGENT_MAX_LEAD_FIELD_LENGTH", 255)
MAX_LEAD_MESSAGE_LENGTH = getattr(settings, "AI_AGENT_MAX_LEAD_MESSAGE_LENGTH", 1200)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def rate_limit_key(request, agent_id, scope):
    session_key = request.session.session_key or "anonymous"
    raw = f"{scope}:{agent_id}:{client_ip(request)}:{session_key}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"ai-agent-rate:{digest}"


def is_rate_limited(request, agent_id, scope, limit, window_seconds):
    key = rate_limit_key(request, agent_id, scope)
    current = cache.get(key, 0)
    if current >= limit:
        return True
    if current == 0:
        cache.set(key, 1, window_seconds)
    else:
        cache.incr(key)
    return False


def clean_text(value, max_length=MAX_LEAD_FIELD_LENGTH):
    value = re.sub(r"\s+", " ", (value or "").strip())
    return value[:max_length]


def clean_message(value, max_length=MAX_LEAD_MESSAGE_LENGTH):
    value = (value or "").strip()
    return value[:max_length]


def valid_email_or_blank(value):
    if not value:
        return True
    try:
        validate_email(value)
    except ValidationError:
        return False
    return True


def valid_phone_or_blank(value):
    if not value:
        return True
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 20


def is_spam_honeypot(request):
    return bool(clean_text(request.POST.get("website_url") or request.POST.get("company_url")))
