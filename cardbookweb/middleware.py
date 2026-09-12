import logging
import time
import uuid

from django.conf import settings


request_logger = logging.getLogger("cardbook.requests")


class WebsiteSubdomainMiddleware:
    reserved_path_prefixes = (
        "/admin/",
        "/api/",
        "/android/",
        "/about/",
        "/business/",
        "/c/",
        "/contact/",
        "/dashboard/",
        "/empresas/",
        "/forms/",
        "/health/",
        "/job/",
        "/login/",
        "/media/",
        "/pricing/",
        "/privacy/",
        "/register/",
        "/site/",
        "/static/",
        "/terms/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        subdomain = self.website_subdomain(request)
        if subdomain and self.should_route_to_website(request.path_info):
            path = request.path_info.strip("/")
            request.cardbook_website_subdomain = subdomain
            request.path_info = f"/site/{subdomain}/" if not path else f"/site/{subdomain}/{path}/"
            request.META["PATH_INFO"] = request.path_info
        return self.get_response(request)

    def website_subdomain(self, request):
        base_domain = getattr(settings, "CARDBOOK_PUBLIC_SITE_BASE_DOMAIN", "")
        if not base_domain:
            return ""

        host = request.get_host().split(":", 1)[0].lower()
        base_domain = base_domain.lower().lstrip(".")
        if host in {base_domain, f"www.{base_domain}"}:
            return ""
        if not host.endswith(f".{base_domain}"):
            return ""

        subdomain = host[: -(len(base_domain) + 1)].strip(".")
        if not subdomain or "." in subdomain:
            return ""
        if subdomain in getattr(settings, "CARDBOOK_RESERVED_SUBDOMAINS", ()):
            return ""
        return subdomain

    def should_route_to_website(self, path):
        normalized_path = path if path.startswith("/") else f"/{path}"
        if normalized_path == "/":
            return True
        return not any(normalized_path.startswith(prefix) for prefix in self.reserved_path_prefixes)


class RequestIDMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header_name = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or uuid.uuid4().hex
        request.cardbook_request_id = request_id
        started_at = time.monotonic()

        try:
            response = self.get_response(request)
        except Exception:
            elapsed_ms = self.elapsed_ms(started_at)
            self.log_request(request, request_id, 500, elapsed_ms, exc_info=True)
            raise

        if getattr(settings, "CARDBOOK_ENABLE_REQUEST_ID_HEADERS", True):
            response[self.response_header_name] = request_id

        elapsed_ms = self.elapsed_ms(started_at)
        self.log_request(request, request_id, response.status_code, elapsed_ms)
        return response

    def elapsed_ms(self, started_at):
        return int((time.monotonic() - started_at) * 1000)

    def should_log(self, request, status_code, elapsed_ms):
        if not getattr(settings, "CARDBOOK_REQUEST_LOGGING_ENABLED", False):
            return False

        path = getattr(request, "path", "")
        excluded_prefixes = getattr(settings, "CARDBOOK_REQUEST_LOG_EXCLUDED_PREFIXES", ())
        if any(path.startswith(prefix) for prefix in excluded_prefixes):
            return False

        slow_request_ms = getattr(settings, "CARDBOOK_SLOW_REQUEST_MS", 1000)
        return status_code >= 400 or elapsed_ms >= slow_request_ms

    def log_request(self, request, request_id, status_code, elapsed_ms, exc_info=False):
        if not self.should_log(request, status_code, elapsed_ms):
            return

        user = getattr(request, "user", None)
        user_id = getattr(user, "pk", None) if getattr(user, "is_authenticated", False) else None
        payload = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "status": status_code,
            "duration_ms": elapsed_ms,
            "user_id": user_id,
            "remote_addr": request.META.get("REMOTE_ADDR", ""),
        }
        level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        request_logger.log(level, "request %s", payload, exc_info=exc_info)
