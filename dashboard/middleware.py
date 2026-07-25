from django.contrib import messages
from django.shortcuts import redirect

from .access_policy import can_access_dashboard_section, default_dashboard_url, section_for_url_name


class DashboardAccessPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.path_info.startswith("/dashboard/"):
            return None
        if not request.user.is_authenticated:
            return None
        url_name = request.resolver_match.url_name if request.resolver_match else ""
        section = section_for_url_name(url_name)
        if can_access_dashboard_section(request.user, section):
            return None
        messages.error(request, "Esta opcion no esta disponible para tu tipo de cuenta.")
        return redirect(default_dashboard_url(request.user))
