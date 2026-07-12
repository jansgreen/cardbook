from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAgentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "agent_profile")
            and request.user.agent_profile.is_active
        )


class IsAdminOrAgentOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        agent = getattr(request.user, "agent_profile", None)
        if not agent:
            return False
        return getattr(obj, "agent_id", None) == agent.id or getattr(getattr(obj, "agent", None), "id", None) == agent.id
