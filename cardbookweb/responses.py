from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response(
        {"success": True, "message": message, "data": data if data is not None else {}},
        status=status_code,
    )


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"success": False, "message": message, "errors": errors if errors is not None else {}},
        status=status_code,
    )


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return success_response(
            "Results retrieved successfully.",
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            },
        )
