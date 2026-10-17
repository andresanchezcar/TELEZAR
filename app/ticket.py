"""Ticket del certificado como imagen PNG (logo, datos y QR) para imprimir.

Se compone con Pillow (dependencia de reportlab/qrcode). El diseno es una
tarjeta horizontal con los datos clave a la izquierda y el codigo QR a la
derecha, lista para abrir o imprimir desde el panel de administracion.
"""
import io
import os

try:
    from PIL import Image, ImageDraw, ImageFont

    _HAVE_PIL = True
except Exception:  # pragma: no cover
    _HAVE_PIL = False


PRIMARY = (12, 28, 70)
ACCENT = (10, 143, 176)
GRAY = (91, 107, 131)
TEXT = (28, 36, 52)
BORDER = (227, 233, 242)
SOFT = (238, 242, 251)

_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
]


def _find_fonts():
    for regular, bold in _FONT_CANDIDATES:
        if os.path.isfile(regular) and os.path.isfile(bold):
            return regular, bold
    for regular, bold in _FONT_CANDIDATES:
        if os.path.isfile(regular):
            return regular, regular
    return None, None


_REGULAR, _BOLD = _find_fonts()
_FONT_CACHE = {}


def _font(size, bold=False):
    key = (size, bold)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    path = _BOLD if bold else _REGULAR
    font = None
    if path:
        try:
            font = ImageFont.truetype(path, size)
        except Exception:
            font = None
    if font is None:
        try:
            font = ImageFont.load_default(size)
        except Exception:
            font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _paste_logo(img, logo_path, x, y, max_w, max_h):
    """Pega el logo escalado y devuelve (ancho, alto) o (0, 0)."""
    if not logo_path:
        return 0, 0
    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception:
        return 0, 0
    if not logo.width or not logo.height:
        return 0, 0
    ratio = min(max_w / logo.width, max_h / logo.height)
    size = (max(1, int(logo.width * ratio)), max(1, int(logo.height * ratio)))
    logo = logo.resize(size, Image.LANCZOS)
    img.paste(logo, (x, y), logo)
    return logo.width, logo.height


def build_ticket_png(cert, settings, qr_bytes=None, logo_path=None):
    """Devuelve los bytes PNG del ticket o None si Pillow no esta disponible."""
    if not _HAVE_PIL:
        return None

    width, height = 1000, 452
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Marco y barra superior.
    draw.rectangle([0, 0, width - 1, height - 1], outline=BORDER, width=2)
    draw.rectangle([0, 0, width, 12], fill=PRIMARY)
    draw.rectangle([0, 0, 270, 12], fill=ACCENT)

    # Encabezado: logo + nombre de la empresa.
    x = 42
    y = 36
    logo_w, logo_h = _paste_logo(img, logo_path, x, y, 150, 58)
    text_x = x + (logo_w + 18 if logo_w else 0)
    name = settings.get("site_name", "TELEZAR COMUNICACIONES")
    draw.text((text_x, y + 4), name, font=_font(23, True), fill=PRIMARY)
    nit = settings.get("company_nit")
    if nit:
        draw.text((text_x, y + 34), "NIT: " + str(nit), font=_font(13), fill=GRAY)

    # Titulo del ticket.
    draw.text((42, 128), "TICKET DE CERTIFICADO", font=_font(17, True), fill=ACCENT)

    # QR a la derecha.
    qr_size = 200
    qx = width - 42 - qr_size
    qy = 62
    draw.rectangle(
        [qx - 12, qy - 12, qx + qr_size + 12, qy + qr_size + 12],
        outline=BORDER,
        width=2,
    )
    if qr_bytes:
        try:
            qr = Image.open(io.BytesIO(qr_bytes)).convert("RGB")
            qr = qr.resize((qr_size, qr_size), Image.LANCZOS)
            img.paste(qr, (qx, qy))
        except Exception:
            pass
    draw.text(
        (qx, qy + qr_size + 20),
        "Escanee para verificar",
        font=_font(13),
        fill=GRAY,
    )

    # Datos a la izquierda.
    fields = [
        ("N° de certificado", cert.code or cert.verify_code),
        ("N° de serie", cert.serial),
        ("Equipo", cert.equipment),
        ("Modelo", cert.equipment_model),
        (
            "Fecha de certificación",
            cert.issued_date.strftime("%d/%m/%Y") if cert.issued_date else "",
        ),
        (
            "Fecha de vencimiento",
            cert.next_date.strftime("%d/%m/%Y") if cert.next_date else "",
        ),
    ]
    fy = 162
    row_h = 44
    for label, value in fields:
        draw.text((42, fy), label.upper(), font=_font(11, True), fill=GRAY)
        draw.text((42, fy + 16), (value or "—"), font=_font(17, True), fill=TEXT)
        fy += row_h

    # Pie.
    draw.line([(42, height - 44), (width - 42, height - 44)], fill=BORDER, width=1)
    parts = []
    if settings.get("phone"):
        parts.append("Tel: " + str(settings["phone"]))
    if settings.get("email_general"):
        parts.append(str(settings["email_general"]))
    if settings.get("address"):
        parts.append(str(settings["address"]))
    draw.text(
        (42, height - 32),
        "   ·   ".join(parts) if parts else name,
        font=_font(12),
        fill=GRAY,
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
