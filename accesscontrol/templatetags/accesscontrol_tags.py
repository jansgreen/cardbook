from django import template

from accesscontrol.permissions import user_can_manage_accesses


register = template.Library()


@register.simple_tag
def can_manage_accesses(user):
    return user_can_manage_accesses(user)
