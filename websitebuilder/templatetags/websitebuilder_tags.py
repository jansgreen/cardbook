from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def translated_title(obj, language):
    translation = obj.translations.filter(language=language).first() if hasattr(obj, "translations") else None
    return getattr(translation, "title", "") or getattr(obj, "title", "")


@register.filter
def translated_subtitle(obj, language):
    translation = obj.translations.filter(language=language).first() if hasattr(obj, "translations") else None
    return getattr(translation, "subtitle", "") or getattr(obj, "subtitle", "")


@register.simple_tag
def block_text(component, key, language="es"):
    block = component.blocks.filter(key=key, is_active=True).first()
    if not block:
        return ""
    translation = block.translations.filter(language=language).first()
    if translation:
        return translation.text or translation.value or translation.button_text
    return block.text or block.value or block.button_text


@register.simple_tag
def block_url(component, key):
    block = component.blocks.filter(key=key, is_active=True).first()
    return block.url if block else ""

@register.simple_tag
def block_value(component, key, language="es"):
    block = component.blocks.filter(key=key, is_active=True).first()
    if not block:
        return ""
    translation = block.translations.filter(language=language).first()
    if translation:
        return translation.value or translation.text or translation.button_text
    return block.value or block.text or block.button_text


@register.filter
def translated_block_text(block, language):
    translation = block.translations.filter(language=language).first()
    if translation:
        return translation.button_text or translation.text or translation.value
    return block.button_text or block.text or block.value


@register.filter
def hero_slides(section):
    slides = []
    components = section.components.filter(is_active=True).prefetch_related("blocks")
    for component in components:
        for block in component.blocks.all():
            if block.is_active and block.block_type == "image" and block.image:
                slides.append(block)
    return slides


SERVICE_ICONS = {
    "briefcase": '<path d="M9 6V5a3 3 0 0 1 3-3h0a3 3 0 0 1 3 3v1"/><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><path d="M3 12h18"/><path d="M10 12v2h4v-2"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5 5L3 18l3 3 6.7-6.7a4 4 0 0 0 5-5l-2.8 2.8-3-3Z"/>',
    "scissors": '<circle cx="6" cy="7" r="3"/><circle cx="6" cy="17" r="3"/><path d="M20 4 8.1 15.9"/><path d="M8.1 8.1 20 20"/>',
    "car": '<path d="M5 17h14"/><path d="M6 17v2"/><path d="M18 17v2"/><path d="M4 13l2-5h12l2 5"/><path d="M5 13h14v4H5Z"/><circle cx="8" cy="15" r="1"/><circle cx="16" cy="15" r="1"/>',
    "laptop": '<path d="M5 4h14v10H5Z"/><path d="M3 18h18"/><path d="M8 18h8"/>',
    "brush": '<path d="M18 3 9 12"/><path d="M8 13c-2 0-4 2-4 5 2 0 5-.4 6-2a2.4 2.4 0 0 0-2-3Z"/><path d="m14 7 3 3"/>',
    "home": '<path d="M3 11 12 3l9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>',
    "heart": '<path d="M20.8 5.6a5.2 5.2 0 0 0-7.4 0L12 7l-1.4-1.4a5.2 5.2 0 0 0-7.4 7.4L12 21l8.8-8a5.2 5.2 0 0 0 0-7.4Z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-5"/>',
    "package": '<path d="m3 7 9-4 9 4-9 4Z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7l.5 3a2 2 0 0 1-.6 1.8L7.7 9.8a16 16 0 0 0 6.5 6.5l1.3-1.3a2 2 0 0 1 1.8-.6l3 .5a2 2 0 0 1 1.7 2Z"/>',
    "star": '<path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2L5.8 21 7 14.2 2 9.3l6.9-1Z"/>',
}


@register.simple_tag
def service_icon_svg(icon_name):
    paths = SERVICE_ICONS.get(icon_name or "briefcase", SERVICE_ICONS["briefcase"])
    return mark_safe(
        f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        f'<g fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'
        f'</svg>'
    )
