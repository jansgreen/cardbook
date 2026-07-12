import re

from rest_framework import serializers

from .services import can_manage_website_builder, website_public_url, website_publish_status
from .models import (
    Block,
    BlockTranslation,
    Component,
    ComponentTranslation,
    Layout,
    Page,
    PageTranslation,
    Section,
    SectionTranslation,
    Theme,
    Website,
)


COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ALLOWED_FONTS = {
    "Inter, system-ui, sans-serif",
    "Poppins, system-ui, sans-serif",
    "Georgia, serif",
    "Montserrat, system-ui, sans-serif",
}


def validate_hex_color(value, field_name):
    if value and not COLOR_RE.match(value):
        raise serializers.ValidationError({field_name: "Use a valid hex color like #0b5ed7."})


def validate_managed_company(request, company, message):
    if request and not can_manage_website_builder(request.user, company):
        raise serializers.ValidationError(message)


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "slug"]


class WebsiteSerializer(serializers.ModelSerializer):
    public_url = serializers.SerializerMethodField()
    publish_status = serializers.SerializerMethodField()

    class Meta:
        model = Website
        fields = "__all__"
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def validate_company(self, company):
        request = self.context.get("request")
        validate_managed_company(request, company, "You do not have permission to manage this company website.")
        return company

    def validate(self, attrs):
        request = self.context.get("request")
        for field_name in ("primary_color", "secondary_color", "accent_color"):
            validate_hex_color(attrs.get(field_name), field_name)
        font_family = attrs.get("font_family")
        if font_family and font_family not in ALLOWED_FONTS:
            raise serializers.ValidationError({"font_family": "This font is not available."})
        if request and not request.user.is_staff:
            if "custom_js" in attrs or attrs.get("custom_js_enabled"):
                raise serializers.ValidationError({"custom_js": "Custom JavaScript is restricted to administrators."})
        return attrs

    def get_public_url(self, obj):
        return website_public_url(self.context.get("request"), obj)

    def get_publish_status(self, obj):
        return website_publish_status(obj)


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_website(self, website):
        request = self.context.get("request")
        validate_managed_company(request, website.company, "You do not have permission to manage this website.")
        return website


class LayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layout
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_page(self, page):
        request = self.context.get("request")
        validate_managed_company(request, page.website.company, "You do not have permission to manage this page layout.")
        return page


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_layout(self, layout):
        request = self.context.get("request")
        validate_managed_company(request, layout.page.website.company, "You do not have permission to manage this section.")
        return layout

    def validate(self, attrs):
        validate_hex_color(attrs.get("background_color"), "background_color")
        return attrs


class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_section(self, section):
        request = self.context.get("request")
        validate_managed_company(request, section.layout.page.website.company, "You do not have permission to manage this component.")
        return section


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_component(self, component):
        request = self.context.get("request")
        validate_managed_company(request, component.section.layout.page.website.company, "You do not have permission to manage this block.")
        return component


class PageTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTranslation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_page(self, page):
        request = self.context.get("request")
        validate_managed_company(request, page.website.company, "You do not have permission to manage this page translation.")
        return page


class SectionTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionTranslation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_section(self, section):
        request = self.context.get("request")
        validate_managed_company(request, section.layout.page.website.company, "You do not have permission to manage this section translation.")
        return section


class ComponentTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentTranslation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_component(self, component):
        request = self.context.get("request")
        validate_managed_company(request, component.section.layout.page.website.company, "You do not have permission to manage this component translation.")
        return component


class BlockTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockTranslation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_block(self, block):
        request = self.context.get("request")
        validate_managed_company(request, block.component.section.layout.page.website.company, "You do not have permission to manage this block translation.")
        return block


class PublicBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id", "block_type", "key", "value", "text", "image", "video", "icon", "url", "button_text", "order", "settings"]


class PublicComponentSerializer(serializers.ModelSerializer):
    blocks = serializers.SerializerMethodField()

    class Meta:
        model = Component
        fields = ["id", "component_type", "name", "title", "subtitle", "order", "settings", "blocks"]

    def get_blocks(self, obj):
        blocks = obj.blocks.filter(is_active=True)
        return PublicBlockSerializer(blocks, many=True, context=self.context).data


class PublicSectionSerializer(serializers.ModelSerializer):
    components = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "section_type", "html_tag", "name", "title", "subtitle", "background_color", "background_image", "order", "settings", "components"]

    def get_components(self, obj):
        components = obj.components.filter(is_active=True)
        return PublicComponentSerializer(components, many=True, context=self.context).data


class PublicPageSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "seo_title", "seo_description", "is_homepage", "sections"]

    def get_sections(self, obj):
        layout = getattr(obj, "layout", None)
        if not layout or not layout.is_active:
            return []
        sections = layout.sections.filter(is_active=True).prefetch_related("components__blocks")
        return PublicSectionSerializer(sections, many=True, context=self.context).data


class PublicWebsiteSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    page = serializers.SerializerMethodField()
    menu = serializers.SerializerMethodField()

    class Meta:
        model = Website
        fields = ["id", "title", "slug", "company_name", "primary_color", "secondary_color", "accent_color", "font_family", "show_header", "show_nav", "page", "menu"]

    def get_page(self, obj):
        page = self.context.get("page")
        return PublicPageSerializer(page, context=self.context).data if page else None

    def get_menu(self, obj):
        return [{"title": page.title, "slug": page.slug, "is_homepage": page.is_homepage} for page in obj.pages.filter(is_published=True, show_in_menu=True)]
