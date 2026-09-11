import base64
from functools import lru_cache
import re
from dataclasses import dataclass
from html import escape
from mimetypes import guess_type

import qrcode
from django.contrib.staticfiles import finders
from django.http import HttpResponse


QR_SHAPE_DIAMOND = "diamond"
QR_SHAPE_DOT = "dot"
QR_SHAPE_SQUARE = "square"
QR_SHAPES = {QR_SHAPE_DIAMOND, QR_SHAPE_DOT, QR_SHAPE_SQUARE}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class QRStyle:
    dot_color: str = "#003875"
    marker_color: str = "#0057b8"
    background_color: str = "#ffffff"
    shape: str = QR_SHAPE_DIAMOND
    radius: int = 22


def safe_hex_color(value, fallback):
    return value if value and HEX_COLOR_RE.match(value) else fallback


def style_from_object(obj, fallback=None):
    fallback = fallback or QRStyle()
    return QRStyle(
        dot_color=safe_hex_color(getattr(obj, "qr_dot_color", None), fallback.dot_color),
        marker_color=safe_hex_color(getattr(obj, "qr_marker_color", None), fallback.marker_color),
        background_color=safe_hex_color(getattr(obj, "qr_background_color", None), fallback.background_color),
        shape=getattr(obj, "qr_shape", fallback.shape) if getattr(obj, "qr_shape", fallback.shape) in QR_SHAPES else fallback.shape,
        radius=fallback.radius,
    )


@lru_cache(maxsize=16)
def static_image_data_uri(static_path):
    resolved_path = finders.find(static_path)
    if not resolved_path:
        return ""
    mime_type = guess_type(resolved_path)[0] or "image/png"
    with open(resolved_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def is_finder_zone(row, col, size):
    return (
        (row < 9 and col < 9)
        or (row < 9 and col >= size - 8)
        or (row >= size - 8 and col < 9)
    )


def render_styled_qr_svg(data, style=None, logo_url=""):
    style = style or QRStyle()
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    module = 10
    matrix_size = len(matrix)
    canvas_size = matrix_size * module
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_size} {canvas_size}" role="img">',
        f'<rect width="{canvas_size}" height="{canvas_size}" rx="{style.radius}" fill="{style.background_color}"/>',
    ]

    for row, line in enumerate(matrix):
        for col, enabled in enumerate(line):
            if not enabled:
                continue

            x = col * module
            y = row * module
            cx = x + module / 2
            cy = y + module / 2

            if is_finder_zone(row, col, matrix_size):
                elements.append(
                    f'<rect x="{x + 1}" y="{y + 1}" width="8" height="8" rx="1.6" fill="{style.marker_color}"/>'
                )
            elif style.shape == QR_SHAPE_DOT:
                elements.append(f'<circle cx="{cx}" cy="{cy}" r="3.8" fill="{style.dot_color}"/>')
            elif style.shape == QR_SHAPE_SQUARE:
                elements.append(
                    f'<rect x="{x + 1.5}" y="{y + 1.5}" width="7" height="7" rx="1.2" fill="{style.dot_color}"/>'
                )
            else:
                elements.append(
                    f'<rect x="{cx - 3.6}" y="{cy - 3.6}" width="7.2" height="7.2" rx=".8" '
                    f'fill="{style.dot_color}" transform="rotate(45 {cx} {cy})"/>'
                )

    if logo_url:
        logo_box_size = canvas_size * 0.23
        logo_size = canvas_size * 0.16
        logo_box_x = (canvas_size - logo_box_size) / 2
        logo_x = (canvas_size - logo_size) / 2
        elements.extend([
            (
                f'<rect x="{logo_box_x:.2f}" y="{logo_box_x:.2f}" width="{logo_box_size:.2f}" '
                f'height="{logo_box_size:.2f}" rx="{logo_box_size * 0.22:.2f}" fill="#ffffff"/>'
            ),
            (
                f'<image href="{escape(logo_url, quote=True)}" x="{logo_x:.2f}" y="{logo_x:.2f}" '
                f'width="{logo_size:.2f}" height="{logo_size:.2f}" preserveAspectRatio="xMidYMid meet"/>'
            ),
        ])

    elements.append("</svg>")
    return "".join(elements)


def qr_svg_response(data, style=None, logo_url=""):
    return HttpResponse(render_styled_qr_svg(data, style, logo_url=logo_url), content_type="image/svg+xml")
