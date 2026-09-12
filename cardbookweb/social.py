import mimetypes

from django.contrib.staticfiles.storage import staticfiles_storage


def absolute_uri(request, url):
    if not url:
        return ""
    if str(url).startswith(("http://", "https://")):
        return str(url)
    return request.build_absolute_uri(str(url))


def image_field_url(request, image_field):
    if not image_field:
        return ""
    try:
        return absolute_uri(request, image_field.url)
    except ValueError:
        return ""


def static_image_url(request, static_path):
    return absolute_uri(request, staticfiles_storage.url(static_path))


def first_image_url(request, *image_fields, fallback_static="img/logo.png"):
    for image_field in image_fields:
        image_url = image_field_url(request, image_field)
        if image_url:
            return image_url
    return static_image_url(request, fallback_static)


def social_image_context(request, *image_fields, fallback_static="img/logo.png"):
    for image_field in image_fields:
        image_url = image_field_url(request, image_field)
        if image_url:
            content_type = mimetypes.guess_type(image_url)[0] or "image/jpeg"
            return {
                "social_image_url": image_url,
                "social_image_type": content_type,
                "social_image_width": getattr(image_field, "width", 1200) or 1200,
                "social_image_height": getattr(image_field, "height", 630) or 630,
            }
    image_url = static_image_url(request, fallback_static)
    return {
        "social_image_url": image_url,
        "social_image_type": mimetypes.guess_type(image_url)[0] or "image/png",
        "social_image_width": 1200,
        "social_image_height": 1200,
    }
