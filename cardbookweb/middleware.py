import uuid

from django.conf import settings


class RequestIDMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header_name = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or uuid.uuid4().hex
        request.cardbook_request_id = request_id

        response = self.get_response(request)
        if getattr(settings, "CARDBOOK_ENABLE_REQUEST_ID_HEADERS", True):
            response[self.response_header_name] = request_id
        return response
