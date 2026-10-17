"""Generacion del certificado en PDF con formato de carta (letter).

Usa reportlab (licencia BSD). El documento incluye: encabezado con logo y datos
de la empresa, titulo, campos del certificado, tabla de estudio, bloque de firma
(con imagen opcional) y codigo QR de verificacion, y un pie de pagina con los
datos de contacto.
"""
import io
from xml.sax.saxutils import escape

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        Image,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.graphics.shapes import Drawing, Line, String, PolyLine, Circle

    REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover
    REPORTLAB_AVAILABLE = False


PRIMARY = "#0c1c46"
ACCENT = "#0a8fb0"
GRAY = "#5b6b83"
BORDER = "#e3e9f2"
TEXT = "#1c2434"
PRIMARY_SOFT = "#eef2fb"


def _styles():
    return {
        "company": ParagraphStyle(
            "company", fontName="Helvetica-Bold", fontSize=13.5,
            textColor=colors.HexColor(PRIMARY), leading=16,
        ),
        "company_sub": ParagraphStyle(
            "company_sub", fontName="Helvetica", fontSize=8.5,
            textColor=colors.HexColor(GRAY), leading=11,
        ),
        "meta": ParagraphStyle(
            "meta", fontName="Helvetica", fontSize=8.5,
            textColor=colors.HexColor(GRAY), leading=11.5, alignment=2,
        ),
        "meta_bold": ParagraphStyle(
            "meta_bold", fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.HexColor(PRIMARY), leading=11.5, alignment=2,
        ),
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=18,
            textColor=colors.HexColor(PRIMARY), leading=22,
            alignment=TA_CENTER, spaceBefore=10, spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=10,
            textColor=colors.HexColor(ACCENT), leading=12.5,
            spaceBefore=0, spaceAfter=0,
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=colors.HexColor(GRAY), leading=9.5,
        ),
        "value": ParagraphStyle(
            "value", fontName="Helvetica-Bold", fontSize=9.5,
            textColor=colors.HexColor(TEXT), leading=12,
        ),
        "th": ParagraphStyle(
            "th", fontName="Helvetica-Bold", fontSize=8.5,
            textColor=colors.HexColor(PRIMARY), leading=10.5,
        ),
        "td": ParagraphStyle(
            "td", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor(TEXT), leading=11.5,
        ),
        "td_center": ParagraphStyle(
            "td_center", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor(TEXT), leading=11.5, alignment=TA_CENTER,
        ),
        "sign_name": ParagraphStyle(
            "sign_name", fontName="Helvetica-Bold", fontSize=10,
            textColor=colors.HexColor(PRIMARY), leading=13,
        ),
        "sign_small": ParagraphStyle(
            "sign_small", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor(GRAY), leading=10.5,
        ),
        "qr_cap": ParagraphStyle(
            "qr_cap", fontName="Helvetica", fontSize=7,
            textColor=colors.HexColor(GRAY), leading=9, alignment=TA_CENTER,
        ),
        "foot": ParagraphStyle(
            "foot", fontName="Helvetica", fontSize=7.5,
            textColor=colors.HexColor(GRAY), leading=10, alignment=TA_CENTER,
        ),
        "legend": ParagraphStyle(
            "legend", fontName="Helvetica", fontSize=7.5,
            textColor=colors.HexColor("#3a4658"), leading=10.5,
            alignment=TA_CENTER,
        ),
        "legal": ParagraphStyle(
            "legal", fontName="Helvetica", fontSize=9.5,
            textColor=colors.HexColor(TEXT), leading=13,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=8.5,
            textColor=colors.HexColor("#1c2434"), leading=11.5,
            leftIndent=12, bulletIndent=2,
        ),
    }


def _esc(value):
    return escape(str(value if value is not None else "")).replace("\n", "<br/>")


def _img(source, max_w, max_h):
    """Crea una imagen escalada dentro de una caja (respeta proporcion)."""
    try:
        image = Image(source)
        iw, ih = image.imageWidth, image.imageHeight
        if not iw or not ih:
            return None
        ratio = min(max_w / iw, max_h / ih)
        image.drawWidth = iw * ratio
        image.drawHeight = ih * ratio
        image.hAlign = "LEFT"
        return image
    except Exception:
        return None


def _kv_table(pairs, styles):
    """Tabla de datos: hasta 2 pares etiqueta/valor por fila."""
    rows = []
    for i in range(0, len(pairs), 2):
        chunk = pairs[i:i + 2]
        row = []
        for label, value in chunk:
            row.append(Paragraph(_esc(label).upper(), styles["label"]))
            row.append(Paragraph(_esc(value) or "—", styles["value"]))
        if len(chunk) == 1:
            row += ["", ""]
        rows.append(row)
    table = Table(rows, colWidths=[100, 155, 100, 155])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor(BORDER)),
    ]))
    return table


SECTION_WIDTH = 532


def _section_heading(title, styles):
    """Encabezado de seccion con barra vertical de acento (estilo web)."""
    heading = Table(
        [["", Paragraph(_esc(title).upper(), styles["section"])]],
        colWidths=[5, SECTION_WIDTH - 5],
    )
    heading.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(ACCENT)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 9),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return heading


def _section(title, flowable, styles):
    body = flowable if isinstance(flowable, (list, tuple)) else [flowable]
    return KeepTogether([
        Spacer(1, 3),
        _section_heading(title, styles),
        Spacer(1, 5),
        *body,
        Spacer(1, 6),
    ])


def _tests_table(tests, styles):
    head = ["Prueba No.", "Longitud de onda (nm)", "Potencia (dBm)",
            "Valor longitud de onda (±0.020 nm)", "Aprobado"]
    rows = [[Paragraph(h, styles["th"]) for h in head]]
    last_row = 0
    if tests:
        for test in tests:
            rows.append([
                Paragraph(_esc(test.test_no), styles["td_center"]),
                Paragraph(_esc(test.wavelength), styles["td"]),
                Paragraph(_esc(test.power), styles["td"]),
                Paragraph(_esc(test.wavelength_value), styles["td"]),
                Paragraph("Sí" if test.approved else "No", styles["td_center"]),
            ])
        last_row = len(rows) - 1
    else:
        rows.append([Paragraph("Sin pruebas registradas.", styles["td_center"]), "", "", "", ""])
        last_row = len(rows) - 1
    table = Table(rows, colWidths=[55, 95, 80, 215, 65], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2fb")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if not tests:
        style.append(("SPAN", (0, last_row), (-1, last_row)))
    table.setStyle(TableStyle(style))
    return table


def _otdr_table(headers, rows, widths, styles):
    data = [[Paragraph(h, styles["th"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(_esc(cell), styles["td"] if i == 0 else styles["td_center"])
                     for i, cell in enumerate(row)])
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2fb")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _bullets(items, styles):
    return [Paragraph(_esc(item), styles["bullet"], bulletText="•") for item in items]


def _legal_box(text, styles):
    """Texto legal dentro de una caja resaltada (estilo web)."""
    table = Table([[Paragraph(_esc(text), styles["legal"])]], colWidths=[SECTION_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PRIMARY_SOFT)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _line_chart_drawing(chart, *, width=470, height=205):
    """Grafica de lineas (multi-serie) con ejes numericos para el PDF."""
    from app.cert_otdr import _axis_values, nice_bounds

    if not isinstance(chart, dict):
        chart = {}
    series = chart.get("series") or []

    points_by_series = []
    all_x, all_y = [], []
    for serie in series:
        pts = []
        for point in serie.get("points") or []:
            if len(point) < 2 or point[0] is None or point[1] is None:
                continue
            x, y = float(point[0]), float(point[1])
            pts.append((x, y))
            all_x.append(x)
            all_y.append(y)
        points_by_series.append((serie.get("name", ""), pts, float(serie.get("z") or 0)))

    if not all_x or not all_y:
        return None

    pad_l, pad_r, pad_t, pad_b = 54, 16, 18, 38
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def resolve(axis, values, fallback_zero):
        ticks = chart.get(axis + "_ticks")
        labels = chart.get(axis + "_tick_labels")
        bounds = chart.get(axis + "_axis")
        if ticks:
            nums = [float(v) for v in ticks if v is not None]
            if labels and len(labels) == len(nums):
                return list(zip(nums, [str(label) for label in labels]))
            step = bounds[2] if bounds else None
            return [(num, _chart_label(num, step)) for num in nums]
        if bounds:
            nums = _axis_values(bounds)
            if labels and len(labels) == len(nums):
                return list(zip(nums, [str(label) for label in labels]))
            return [(num, _chart_label(num, bounds[2])) for num in nums]
        nice = nice_bounds(min(values), max(values), zero=fallback_zero)
        return [(num, _chart_label(num, nice[2])) for num in _axis_values(nice)]

    x_ticks = resolve("x", all_x, True)
    y_ticks = resolve("y", all_y, True)

    x_values = all_x + [t for t, _ in x_ticks]
    y_values = all_y + [t for t, _ in y_ticks]
    x0, x1 = min(x_values), max(x_values)
    y0, y1 = min(y_values), max(y_values)
    if x1 == x0:
        x1 = x0 + 1
    if y1 == y0:
        y1 = y0 + 1
    margin = (x1 - x0) * 0.06
    x0 -= margin
    x1 += margin

    def x_at(value):
        return pad_l + plot_w * (value - x0) / (x1 - x0)

    def y_at(value):
        return pad_t + plot_h * (y1 - value) / (y1 - y0)

    drawing = Drawing(width, height)
    grid = colors.HexColor(BORDER)
    axis = colors.HexColor(PRIMARY)
    muted = colors.HexColor(GRAY)

    # Rejilla y etiquetas del eje Y.
    for value, label in y_ticks:
        if value < y0 or value > y1:
            continue
        y = y_at(value)
        drawing.add(Line(pad_l, y, pad_l + plot_w, y, strokeColor=grid, strokeWidth=0.6))
        text = String(pad_l - 5, y - 3, label)
        text.fontName = "Helvetica"
        text.fontSize = 6.5
        text.fillColor = muted
        text.textAnchor = "end"
        drawing.add(text)

    # Rejilla y etiquetas del eje X.
    for value, label in x_ticks:
        if value < x0 or value > x1:
            continue
        x = x_at(value)
        drawing.add(Line(x, pad_t, x, pad_t + plot_h, strokeColor=grid, strokeWidth=0.6))
        text = String(x, pad_t + plot_h + 12, label)
        text.fontName = "Helvetica"
        text.fontSize = 6.5
        text.fillColor = muted
        text.textAnchor = "middle"
        drawing.add(text)

    # Ejes.
    drawing.add(Line(pad_l, pad_t, pad_l, pad_t + plot_h, strokeColor=axis, strokeWidth=1))
    drawing.add(Line(pad_l, pad_t + plot_h, pad_l + plot_w, pad_t + plot_h,
                     strokeColor=axis, strokeWidth=1))

    # Series con desplazamiento pseudo-3D en X.
    palette = [ACCENT, "#e52421", "#2f8f5b", "#b8962f", "#7a4fd0", "#e07b00"]
    depth = 0.03
    for index, (_, pts, z) in enumerate(points_by_series):
        color = colors.HexColor(palette[index % len(palette)])
        dx = z * depth * plot_w
        if len(pts) >= 2:
            coords = []
            for x, y in pts:
                coords += [x_at(x) + dx, y_at(y)]
            drawing.add(PolyLine(coords, strokeColor=color, strokeWidth=1.4))
        for x, y in pts:
            drawing.add(Circle(x_at(x) + dx, y_at(y), 2.2, fillColor=colors.white,
                               strokeColor=color, strokeWidth=1.1))

    # Leyenda (solo si hay mas de una serie).
    visible = [(name, pts, z) for name, pts, z in points_by_series if pts]
    if len(visible) > 1:
        ly = pad_t + plot_h - 4
        for index, (name, _, z) in enumerate(visible):
            color = colors.HexColor(palette[index % len(palette)])
            drawing.add(Line(pad_l + 8, ly, pad_l + 24, ly, strokeColor=color, strokeWidth=2))
            text = String(pad_l + 28, ly - 3, str(name))
            text.fontName = "Helvetica"
            text.fontSize = 6.5
            text.fillColor = muted
            drawing.add(text)
            ly -= 11

    if chart.get("x_title"):
        cap = String(pad_l + plot_w / 2, 6, str(chart["x_title"]))
        cap.fontName = "Helvetica-Bold"
        cap.fontSize = 7
        cap.fillColor = axis
        cap.textAnchor = "middle"
        drawing.add(cap)
    if chart.get("y_title"):
        cap = String(8, pad_t + plot_h / 2, str(chart["y_title"]))
        cap.fontName = "Helvetica-Bold"
        cap.fontSize = 7
        cap.fillColor = axis
        drawing.add(cap)
    return drawing


def _chart_label(value, step):
    if step and step >= 1:
        return f"{value:.0f}"
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _chart_3d(chart, kind):
    """Grafica 3D (matplotlib -> PNG) o ``None`` si no esta disponible."""
    try:
        from app import chart3d
    except Exception:
        return None
    png = chart3d.render(chart, kind=kind, fmt="png", dpi=160)
    if not png:
        return None
    try:
        image = Image(io.BytesIO(png))
    except Exception:
        return None
    iw, ih = image.imageWidth, image.imageHeight
    if not iw or not ih:
        return None
    max_w, max_h = 300, 190
    ratio = min(max_w / iw, max_h / ih)
    image.drawWidth = iw * ratio
    image.drawHeight = ih * ratio
    image.hAlign = "CENTER"
    return image


def _distance_chart_3d(chart):
    """Grafica 3D de distancia (matplotlib -> PNG) o ``None`` si no hay."""
    return _chart_3d(chart, "distance")


def _attenuation_chart_3d(chart):
    """Grafica 3D de atenuaciones (matplotlib -> PNG) o ``None`` si no hay."""
    return _chart_3d(chart, "attenuation")



def _otdr_story(view, styles):
    """Secciones del certificado OTDR (condiciones, calibraciones y graficas)."""
    story = []

    if view["env_parts"]:
        story.append(_section(
            "Condiciones ambientales",
            _kv_table(view["env_parts"], styles),
            styles,
        ))

    sample_headers = [f"Muestra {i + 1}" for i in range(5)]

    for cal in view["distance"]:
        title = "Calibración distancia"
        if cal["wavelength"]:
            title += f" {cal['wavelength']} nm"
        headers = ["Patrón", "Valor inicial"] + sample_headers + ["Promedio", "Desv. ST"]
        rows = [
            [r["pattern"], r["initial"]] + r["samples"] + [r["mean"], r["stdev"]]
            for r in cal["rows"]
        ]
        widths = [52, 42] + [40] * 5 + [44, 66]
        body = [_otdr_table(headers, rows, widths, styles)] if rows else [
            Paragraph("Sin datos registrados.", styles["td_center"])
        ]
        chart = _distance_chart_3d(cal["chart"]) or _line_chart_drawing(cal["chart"])
        if chart is not None:
            body.append(Spacer(1, 8))
            body.append(chart)
        story.append(_section(title, body, styles))

    for cal in view["attenuation"]:
        title = "Calibración atenuaciones"
        if cal["wavelength"]:
            title += f" {cal['wavelength']} nm"
        headers = ["Evento", "Valor patrón"] + sample_headers + ["Promedio", "Desv. ST"]
        rows = [
            [r["event"], r["pattern"]] + r["samples"] + [r["mean"], r["stdev"]]
            for r in cal["rows"]
        ]
        widths = [58, 42] + [40] * 5 + [44, 66]
        body = [_otdr_table(headers, rows, widths, styles)] if rows else [
            Paragraph("Sin datos registrados.", styles["td_center"])
        ]
        chart = _attenuation_chart_3d(cal["chart"]) or _line_chart_drawing(cal["chart"])
        if chart is not None:
            body.append(Spacer(1, 8))
            body.append(chart)
        story.append(_section(title, body, styles))

    if view["patterns"]:
        story.append(_section("Patrones utilizados", _bullets(view["patterns"], styles), styles))

    if view["methods"]:
        story.append(_section("Métodos utilizados", _bullets(view["methods"], styles), styles))

    return story


def _header(cert, settings, styles, logo_path):
    logo = _img(logo_path, 130, 56) if logo_path else None
    company_lines = [Paragraph(_esc(settings.get("site_name", "TELEZAR COMUNICACIONES")), styles["company"])]
    if settings.get("company_nit"):
        company_lines.append(Paragraph("NIT: " + _esc(settings["company_nit"]), styles["company_sub"]))
    if settings.get("company_legal_rep"):
        company_lines.append(
            Paragraph(_esc(settings["company_legal_rep"]), styles["company_sub"])
        )

    left_content = []
    if logo:
        logo.hAlign = "LEFT"
        left_content.append(logo)
    left_content += company_lines

    right_cells = []
    if cert.code:
        right_cells.append(Paragraph("Código: " + _esc(cert.code), styles["meta_bold"]))
    if cert.device_type:
        right_cells.append(Paragraph("Dispositivo: " + _esc(cert.device_label), styles["meta"]))
    if cert.issued_date:
        right_cells.append(Paragraph("Emitido: " + cert.issued_date.strftime("%d/%m/%Y"), styles["meta"]))

    table = Table([[left_content, right_cells]], colWidths=[330, 202])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 1.6, colors.HexColor(PRIMARY)),
    ]))
    return table


def _signature_block(cert, styles, signature_path, qr_bytes):
    left = [
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor(TEXT),
                   spaceBefore=0, spaceAfter=4),
    ]
    if signature_path:
        sig = _img(signature_path, 300, 140)
        if sig:
            left.append(sig)
    left.append(Paragraph(_esc(cert.certifier) or "&nbsp;", styles["sign_name"]))
    if cert.certifier_role:
        left.append(Paragraph(_esc(cert.certifier_role), styles["sign_small"]))
    left.append(Paragraph("Quien certifica", styles["sign_small"]))

    right = []
    if qr_bytes:
        qr = _img(io.BytesIO(qr_bytes), 82, 82)
        if qr:
            qr.hAlign = "CENTER"
            box = Table([[qr]], colWidths=[96])
            box.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(BORDER)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            right.append(box)
    right.append(Paragraph("Escanee para verificar la validez de este certificado", styles["qr_cap"]))

    table = Table([[left, right]], colWidths=[360, 172])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, 0), "BOTTOM"),
        ("VALIGN", (1, 0), (1, 0), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _footer(settings):
    company = settings.get("site_name", "")
    parts = []
    if settings.get("address"):
        parts.append(settings["address"])
    tel = settings.get("phone") or ""
    if settings.get("phone2"):
        tel = (tel + " / " + settings["phone2"]).strip(" /")
    if tel:
        parts.append("Tel: " + tel)
    for key in ("email_general", "email_ventas"):
        if settings.get(key):
            parts.append(settings[key])
    rest = "   ·   ".join(p for p in parts if p)

    def draw(canvas, doc):
        canvas.saveState()
        width = doc.pagesize[0]
        canvas.setStrokeColor(colors.HexColor(BORDER))
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, 46, width - doc.rightMargin, 46)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(colors.HexColor(PRIMARY))
        canvas.drawString(doc.leftMargin, 36, company)
        if rest:
            offset = canvas.stringWidth(company, "Helvetica-Bold", 7.5) + 14
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(colors.HexColor(GRAY))
            canvas.drawString(doc.leftMargin + offset, 36, rest)
        canvas.restoreState()

    return draw


def build_certificate_pdf(cert, settings, verify_url, logo_path=None,
                          signature_path=None, qr_bytes=None):
    """Devuelve los bytes de un PDF en formato carta para el certificado."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab no esta instalado; no se puede generar el PDF.")

    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"{cert.title or cert.type_label} - {cert.serial}",
        author=settings.get("site_name", ""),
        subject=cert.type_label,
    )

    story = [
        _header(cert, settings, styles, logo_path),
        HRFlowable(width="100%", thickness=1.6, color=colors.HexColor(PRIMARY),
                   spaceBefore=2, spaceAfter=8),
        Paragraph(_esc(cert.title or cert.type_label), styles["title"]),
        Spacer(1, 8),
    ]

    mech = None
    if cert.device_type == "mecanica":
        from app.cert_mech import build_mech_view

        mech = build_mech_view(cert.mech_data)
        if mech["legal"]:
            story.append(_legal_box(mech["legal"], styles))
            story.append(Spacer(1, 8))
        if mech["actions"]:
            story.append(_section("Actividades realizadas", _bullets(mech["actions"], styles), styles))

    client_pairs = [
        ("Razon social", cert.client),
        ("Documento y/o NIT", cert.client_doc),
        ("Correo electronico", cert.client_email),
    ]
    if cert.client_address:
        client_pairs.append(("Direccion", cert.client_address))
    story.append(_section("Datos del cliente", _kv_table(client_pairs, styles), styles))

    equipment_pairs = [
        ("Equipo", cert.equipment),
        ("Marca", cert.equipment_brand),
        ("Modelo", cert.equipment_model),
        ("Numero de serie", cert.serial),
    ]
    if cert.device_type == "opm":
        equipment_pairs += [
            ("Incertidumbre (%)", cert.uncertainty),
            ("Longitud de onda estandar", cert.std_wavelength),
        ]
    equipment_pairs += [
        ("Fecha de calibracion", cert.issued_date.strftime("%d/%m/%Y") if cert.issued_date else ""),
        ("Proxima calibracion", cert.next_date.strftime("%d/%m/%Y") if cert.next_date else ""),
    ]

    story.append(_section("Datos del equipo a certificar", _kv_table(equipment_pairs, styles), styles))

    if cert.device_type == "mecanica" and mech is not None:
        if mech["patrones"]:
            pat_rows = [
                (r.get("descripcion", ""), r.get("fabricante", ""), r.get("modelo", ""),
                 r.get("serie", ""), r.get("certificado", ""), r.get("vence", ""))
                for r in mech["patrones"]
            ]
            story.append(_section(
                "Patrones utilizados",
                _otdr_table(["Descripcion", "Fabricante", "Modelo", "N de serie",
                             "N certificado", "Vence"],
                            pat_rows, [120, 80, 80, 96, 96, 60], styles),
                styles,
            ))
        if mech.get("env_parts"):
            story.append(_section(
                "Condiciones ambientales de ajuste y calibracion",
                _kv_table(mech["env_parts"], styles),
                styles,
            ))

    if cert.device_type == "otdr":
        from app.cert_otdr import build_otdr_view

        view = build_otdr_view(cert.otdr_data)
        story.extend(_otdr_story(view, styles))
        story.append(Spacer(1, 2))
        story.append(Paragraph(_esc(view["legend"]), styles["legend"]))
        story.append(Spacer(1, 10))
    elif cert.device_type == "opm":
        story.append(_section("Estudio de calibracion", _tests_table(cert.tests, styles), styles))

        test_equipments = cert.test_equipments
        test_value = "\n".join(test_equipments) if test_equipments else ""
        story.append(_section("Datos del equipo de prueba", _kv_table([
            ("Equipo de prueba (patrón)", test_value),
        ], styles), styles))
        story.append(Spacer(1, 4))

    story.append(_signature_block(cert, styles, signature_path, qr_bytes))

    if cert.notes:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Notas: " + _esc(cert.notes), styles["foot"]))

    doc.build(story, onFirstPage=_footer(settings), onLaterPages=_footer(settings))
    return buffer.getvalue()
