from .access_policy import dashboard_menu_for_user, dashboard_user_type, section_for_url_name


def dashboard_access_menu(request):
    if not request.user.is_authenticated:
        return {
            "dashboard_menu": [],
            "dashboard_user_type": "",
        }
    url_name = request.resolver_match.url_name if request.resolver_match else ""
    current_section = section_for_url_name(url_name)
    return {
        "dashboard_menu": dashboard_menu_for_user(request.user, current_section=current_section),
        "dashboard_user_type": dashboard_user_type(request.user),
    }
