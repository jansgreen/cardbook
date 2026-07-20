from .guides import get_dashboard_guide_payload


def dashboard_ai_guide(request):
    return {"dashboard_ai_guide": get_dashboard_guide_payload(request)}
