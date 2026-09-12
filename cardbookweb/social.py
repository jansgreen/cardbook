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
