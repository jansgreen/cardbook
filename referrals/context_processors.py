from .services import unread_notification_count, user_notifications


def dashboard_notifications(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "dashboard_unread_notifications": 0,
            "dashboard_recent_notifications": [],
        }
    return {
        "dashboard_unread_notifications": unread_notification_count(request.user),
        "dashboard_recent_notifications": user_notifications(request.user, limit=5),
    }
