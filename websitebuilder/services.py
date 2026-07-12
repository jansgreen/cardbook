from django.db import transaction
from django.urls import reverse

from accesscontrol.services import (
    PERM_MANAGE_WEBSITE_BUILDER,
    PERM_PUBLISH_WEBSITE_BUILDER,
    user_has_access_permission,
)
from companies.permissions import can_manage_company
from .models import Block, Component, Layout, Page, Section, Theme, Website


def get_default_theme():
    theme, _ = Theme.objects.get_or_create(
        slug="cardbook-pro",
        defaults={
            "name": "Cardbook Pro",
            "description": "Tema profesional para pequenas empresas.",
            "primary_color": "#0b5ed7",
            "secondary_color": "#083b75",
            "accent_color": "#d8a441",
            "font_family": "Inter, system-ui, sans-serif",
        },
    )
    return theme


def can_manage_website_builder(user, company):
    if can_manage_company(user, company):
        return True
    return user_has_access_permission(user, PERM_MANAGE_WEBSITE_BUILDER, company)


def can_publish_website_builder(user, company):
    if can_manage_company(user, company):
        return True
    return user_has_access_permission(user, PERM_PUBLISH_WEBSITE_BUILDER, company)


def public_site_path(website, page=None):
    if page and not page.is_homepage:
        return reverse("websitebuilder-public-page", kwargs={"website_slug": website.slug, "page_slug": page.slug})
    return reverse("websitebuilder-public-home", kwargs={"website_slug": website.slug})


def website_public_url(request, website, page=None):
    path = public_site_path(website, page)
    return request.build_absolute_uri(path) if request else path


def website_publish_status(website):
    if not website:
        return {
            "can_publish": False,
            "issues": ["Crea el website inicial."],
            "published_pages": 0,
            "active_sections": 0,
        }

    pages = website.pages.filter(is_active=True)
    published_pages = pages.filter(is_published=True)
    homepage = pages.filter(is_homepage=True).first()
    active_sections = Section.objects.filter(layout__page__website=website, layout__is_active=True, layout__page__is_active=True, is_active=True).count()
    issues = []

    if not homepage:
        issues.append("Define una pagina principal.")
    elif not homepage.is_published:
        issues.append("Publica la pagina principal.")
    if not published_pages.exists():
        issues.append("Publica al menos una pagina.")
    if active_sections == 0:
        issues.append("Agrega al menos una seccion activa.")
    if not website.title.strip():
        issues.append("Define el titulo del sitio.")

    return {
        "can_publish": not issues,
        "issues": issues,
        "published_pages": published_pages.count(),
        "active_sections": active_sections,
    }


@transaction.atomic
def create_starter_website(company, *, title=None, publish=False):
    website, created = Website.objects.get_or_create(
        company=company,
        defaults={
            "title": title or company.name,
            "theme": get_default_theme(),
            "primary_color": "#0b5ed7",
            "secondary_color": "#083b75",
            "accent_color": "#d8a441",
            "font_family": "Inter, system-ui, sans-serif",
            "show_header": True,
            "show_nav": True,
            "meta_title": company.name,
            "meta_description": company.description or "",
            "is_published": publish,
        },
    )
    if not created and website.pages.exists():
        return website

    if not website.theme_id:
        website.theme = get_default_theme()
        website.save(update_fields=["theme", "updated_at"])

    home = Page.objects.create(
        website=website,
        title="Inicio",
        slug="inicio",
        order=1,
        is_homepage=True,
        seo_title=company.name,
        seo_description=company.description or "",
    )
    layout = Layout.objects.create(page=home, layout_type=Layout.LANDING_PAGE, name="Landing principal")

    hero = Section.objects.create(
        layout=layout,
        section_type="hero",
        html_tag=Section.TAG_HEADER,
        name="Hero principal",
        title=company.name,
        subtitle=company.description or "Construimos presencia digital profesional para tu negocio.",
        order=1,
        settings={"align": "left", "size": "large"},
    )
    hero_cta = Component.objects.create(section=hero, component_type="button_group", name="Acciones hero", order=1)
    Block.objects.create(component=hero_cta, block_type="button", key="primary", button_text="Contactar", url="#contacto", order=1)
    if company.website:
        Block.objects.create(component=hero_cta, block_type="link", key="website", button_text="Sitio actual", url=company.website, order=2)

    services = Section.objects.create(
        layout=layout,
        section_type="services",
        html_tag=Section.TAG_SECTION,
        name="Servicios",
        title="Servicios",
        subtitle="Soluciones pensadas para tus clientes.",
        order=2,
        settings={"columns": 3},
    )
    service_items = [item.strip() for item in (company.services or "").replace("\n", ",").split(",") if item.strip()]
    if not service_items:
        service_items = ["Perfil profesional", "Contacto directo", "Soluciones digitales"]
    for index, service in enumerate(service_items[:6], start=1):
        component = Component.objects.create(
            section=services,
            component_type="service_card",
            name=service,
            title=service,
            order=index,
        )
        Block.objects.create(component=component, block_type="text", key="description", text="Servicio disponible para clientes y aliados.", order=1)

    cta = Section.objects.create(
        layout=layout,
        section_type="cta",
        html_tag=Section.TAG_SECTION,
        name="Llamada a la accion",
        title="Listo para conectar con nosotros?",
        subtitle="Comparte tu necesidad y te responderemos pronto.",
        order=3,
    )
    cta_component = Component.objects.create(section=cta, component_type="button_group", name="Botones CTA", order=1)
    Block.objects.create(component=cta_component, block_type="phone", key="phone", button_text="Llamar", value=company.phone_number or "", order=1)
    Block.objects.create(component=cta_component, block_type="email", key="email", button_text="Email", value=company.email or "", order=2)

    footer = Section.objects.create(
        layout=layout,
        section_type="footer",
        html_tag=Section.TAG_FOOTER,
        name="Footer",
        title=company.name,
        subtitle=company.address or company.city or "",
        order=4,
    )
    info = Component.objects.create(section=footer, component_type="contact_info", name="Contacto", order=1)
    Block.objects.create(component=info, block_type="phone", key="phone", value=company.phone_number or "", order=1)
    Block.objects.create(component=info, block_type="email", key="email", value=company.email or "", order=2)
    Block.objects.create(component=info, block_type="address", key="address", value=company.address or "", order=3)
    return website


@transaction.atomic
def duplicate_page(page, *, title=None):
    new_page = Page.objects.create(
        website=page.website,
        title=title or f"Copia de {page.title}",
        slug="",
        icon=page.icon,
        order=page.order + 1,
        is_homepage=False,
        is_published=False,
        show_in_menu=page.show_in_menu,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        og_title=page.og_title,
        twitter_card=page.twitter_card,
    )
    if hasattr(page, "layout"):
        new_layout = Layout.objects.create(
            page=new_page,
            layout_type=page.layout.layout_type,
            name=page.layout.name,
            is_active=page.layout.is_active,
            settings=page.layout.settings,
        )
        for section in page.layout.sections.all():
            new_section = Section.objects.create(
                layout=new_layout,
                section_type=section.section_type,
                html_tag=section.html_tag,
                name=section.name,
                title=section.title,
                subtitle=section.subtitle,
                background_color=section.background_color,
                background_image=section.background_image,
                order=section.order,
                is_active=section.is_active,
                settings=section.settings,
            )
            for component in section.components.all():
                new_component = Component.objects.create(
                    section=new_section,
                    component_type=component.component_type,
                    name=component.name,
                    title=component.title,
                    subtitle=component.subtitle,
                    order=component.order,
                    is_active=component.is_active,
                    settings=component.settings,
                )
                for block in component.blocks.all():
                    Block.objects.create(
                        component=new_component,
                        block_type=block.block_type,
                        key=block.key,
                        value=block.value,
                        text=block.text,
                        image=block.image,
                        video=block.video,
                        icon=block.icon,
                        url=block.url,
                        button_text=block.button_text,
                        order=block.order,
                        is_active=block.is_active,
                        settings=block.settings,
                    )
    return new_page


@transaction.atomic
def duplicate_section(section, *, target_layout=None):
    layout = target_layout or section.layout
    new_section = Section.objects.create(
        layout=layout,
        section_type=section.section_type,
        html_tag=section.html_tag,
        name=f"Copia de {section.name}",
        title=section.title,
        subtitle=section.subtitle,
        background_color=section.background_color,
        background_image=section.background_image,
        order=section.order + 1,
        is_active=False,
        settings=section.settings,
    )
    for component in section.components.all():
        new_component = Component.objects.create(
            section=new_section,
            component_type=component.component_type,
            name=component.name,
            title=component.title,
            subtitle=component.subtitle,
            order=component.order,
            is_active=component.is_active,
            settings=component.settings,
        )
        for block in component.blocks.all():
            Block.objects.create(
                component=new_component,
                block_type=block.block_type,
                key=block.key,
                value=block.value,
                text=block.text,
                image=block.image,
                video=block.video,
                icon=block.icon,
                url=block.url,
                button_text=block.button_text,
                order=block.order,
                is_active=block.is_active,
                settings=block.settings,
            )
    return new_section


@transaction.atomic
def duplicate_component(component, *, target_section=None):
    section = target_section or component.section
    new_component = Component.objects.create(
        section=section,
        component_type=component.component_type,
        name=f"Copia de {component.name}",
        title=component.title,
        subtitle=component.subtitle,
        order=component.order + 1,
        is_active=False,
        settings=component.settings,
    )
    for block in component.blocks.all():
        Block.objects.create(
            component=new_component,
            block_type=block.block_type,
            key=block.key,
            value=block.value,
            text=block.text,
            image=block.image,
            video=block.video,
            icon=block.icon,
            url=block.url,
            button_text=block.button_text,
            order=block.order,
            is_active=block.is_active,
            settings=block.settings,
        )
    return new_component


@transaction.atomic
def duplicate_block(block, *, target_component=None):
    component = target_component or block.component
    return Block.objects.create(
        component=component,
        block_type=block.block_type,
        key=f"{block.key}_copy",
        value=block.value,
        text=block.text,
        image=block.image,
        video=block.video,
        icon=block.icon,
        url=block.url,
        button_text=block.button_text,
        order=block.order + 1,
        is_active=False,
        settings=block.settings,
    )
