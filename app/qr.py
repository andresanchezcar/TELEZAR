"""Generacion de codigos QR con logo opcional en el centro.

La libreria `qrcode` es de codigo abierto (licencia BSD) y usa Pillow para
la manipulacion de imagenes. Para poder incrustar un logo en el centro se
genera el QR con el nivel de correccion de errores mas alto (H), que tolera
hasta ~30% de la superficie cubierta.
"""
import io
import os

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H

    _HAVE_QRCODE = True
except Exception:  # pragma: no cover
    _HAVE_QRCODE = False

try:
    from PIL import Image

    _HAVE_PIL = True
except Exception:  # pragma: no cover
    _HAVE_PIL = False


def qr_available():
    return _HAVE_QRCODE


def qr_png(data, logo_path=None, box_size=10, border=2, logo_ratio=0.22):
    """Devuelve los bytes PNG de un QR. Si `logo_path` existe, lo incrusta
    centrado sobre una placa blanca. Devuelve None si falta la libreria."""
    if not _HAVE_QRCODE:
        return None

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if logo_path and _HAVE_PIL and os.path.isfile(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            target = int(img.width * logo_ratio)
            if logo.width >= logo.height:
                new_w = target
                new_h = max(1, int(logo.height * target / logo.width))
            else:
                new_h = target
                new_w = max(1, int(logo.width * target / logo.height))
            logo = logo.resize((new_w, new_h), Image.LANCZOS)

            pad = max(4, int(target * 0.12))
            plate = Image.new(
                "RGBA", (logo.width + pad * 2, logo.height + pad * 2), (255, 255, 255, 255)
            )
            plate.paste(logo, (pad, pad), logo)

            pos = (
                (img.width - plate.width) // 2,
                (img.height - plate.height) // 2,
            )
            img.paste(plate.convert("RGB"), pos)
        except Exception:
            pass

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
