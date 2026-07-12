from rest_framework import permissions

from companies.permissions import can_access_company
from .models import Block, Component, Layout, Page, Section, Website
from .services import can_manage_website_builder


def website_from_object(obj):
    if isinstance(obj, Website):
        return obj
    if isinstance(obj, Page):
        return obj.website
    if isinstance(obj, Layout):
        return obj.page.website
    if isinstance(obj, Section):
        return obj.layout.page.website
    if isinstance(obj, Component):
        return obj.section.layout.page.website
    if isinstance(obj, Block):
        return obj.component.section.layout.page.website
    return None


def can_access_website(user, website):
    return bool(website and can_access_company(user, website.company))


def can_edit_website(user, website):
    return bool(website and can_manage_website_builder(user, website.company))


class WebsiteOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        website = website_from_object(obj)
        return can_edit_website(request.user, website)


class CanEditWebsitePermission(WebsiteOwnerPermission):
    pass


class PublicWebsitePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True


class CompanyOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        company = getattr(obj, "company", obj)
        return can_manage_website_builder(request.user, company)


class CompanyAdminPermission(CompanyOwnerPermission):
    pass
