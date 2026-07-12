from django import template

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
