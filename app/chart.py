"""Generacion de graficas en SVG (sin dependencias) para la vista web.

Las graficas del PDF se construyen aparte con reportlab (ver app/pdf.py).

Cada grafica recibe un ``chart`` con esta forma::

    {
        "series": [{"name": "Muestra 1", "points": [[x, y], ...], "z": 0}, ...],
        "x_title": "...", "y_title": "...",
        "x_axis": [min, max, paso] | None,
        "y_axis": [min, max, paso] | None,
        "x_ticks": [..] | None, "x_tick_labels": [".."] | None,
        "y_ticks": [..] | None, "y_tick_labels": [".."] | None,
    }

La clave ``z`` de cada serie aplica un pequeno desplazamiento horizontal
(efecto pseudo-3D) para distinguir visualmente las muestras entre si.
"""
from html import escape

from app.cert_otdr import _axis_values, nice_bounds

ACCENT = "#0a8fb0"
PRIMARY = "#0c1c46"
GRID = "#dfe5ef"
MUTED = "#5b6b83"
PALETTE = ["#0a8fb0", "#e52421", "#2f8f5b", "#b8962f", "#7a4fd0", "#e07b00"]
DEPTH = 0.03  # desplazamiento horizontal por unidad de z (pseudo-3D)


def _fmt(value, step=None):
    if value is None:
        return "0"
    if step is not None and step >= 1:
        text = f"{value:.0f}"
    else:
        text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _collect(chart):
    xs, ys = [], []
    for serie in chart.get("series") or []:
        for point in serie.get("points") or []:
            if len(point) < 2:
                continue
            x, y = point[0], point[1]
            if x is None or y is None:
                continue
            xs.append(float(x))
            ys.append(float(y))
    return xs, ys


def _resolve_ticks(chart, axis, values):
    """Devuelve [(valor, etiqueta), ...] para 'x' o 'y'."""
    ticks = chart.get(axis + "_ticks")
    labels = chart.get(axis + "_tick_labels")
    bounds = chart.get(axis + "_axis")
    if ticks:
        nums = [float(v) for v in ticks if v is not None]
        if labels and len(labels) == len(nums):
            return list(zip(nums, [str(label) for label in labels]))
        step = bounds[2] if bounds else None
        return [(num, _fmt(num, step)) for num in nums]
    if bounds:
        nums = _axis_values(bounds)
        if labels and len(labels) == len(nums):
            return list(zip(nums, [str(label) for label in labels]))
        return [(num, _fmt(num, bounds[2])) for num in nums]
    if values:
        nice = nice_bounds(min(values), max(values))
        return [(num, _fmt(num, nice[2])) for num in _axis_values(nice)]
    return []


def line_chart_svg(chart, *, width=560, height=300):
    """Devuelve una grafica de lineas como cadena SVG (auto-contenida)."""
    if not isinstance(chart, dict):
        chart = {}
    series = chart.get("series") or []
    x_title = chart.get("x_title") or ""
    y_title = chart.get("y_title") or ""

    pad_l, pad_r, pad_t, pad_b = 64, 20, 30, 58
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    parts = [
        f'<svg class="otdr-chart" viewBox="0 0 {width} {height}" '
        f'role="img" xmlns="http://www.w3.org/2000/svg">'
    ]

    xs, ys = _collect(chart)
    if not xs or not ys:
        parts.append(
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'fill="{MUTED}" font-size="13">Sin datos para graficar</text></svg>'
        )
        return "".join(parts)

    x_ticks = _resolve_ticks(chart, "x", xs)
    y_ticks = _resolve_ticks(chart, "y", ys)

    x_values = xs + [tick for tick, _ in x_ticks]
    y_values = ys + [tick for tick, _ in y_ticks]
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

    # Rejilla horizontal y etiquetas del eje Y.
    for value, label in y_ticks:
        if value < y0 or value > y1:
            continue
        y = y_at(value)
        parts.append(
            f'<line x1="{pad_l}" y1="{y:.2f}" x2="{pad_l + plot_w}" y2="{y:.2f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{pad_l - 8}" y="{y + 3:.2f}" text-anchor="end" '
            f'fill="{MUTED}" font-size="10">{escape(label)}</text>'
        )

    # Rejilla vertical y etiquetas del eje X.
    for value, label in x_ticks:
        if value < x0 or value > x1:
            continue
        x = x_at(value)
        parts.append(
            f'<line x1="{x:.2f}" y1="{pad_t}" x2="{x:.2f}" y2="{pad_t + plot_h}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{pad_t + plot_h + 18}" text-anchor="middle" '
            f'fill="{MUTED}" font-size="10">{escape(label)}</text>'
        )
        parts.append(
            f'<line x1="{x:.2f}" y1="{pad_t + plot_h}" x2="{x:.2f}" '
            f'y2="{pad_t + plot_h + 4}" stroke="{PRIMARY}" stroke-width="1.2"/>'
        )

    # Ejes.
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" '
        f'stroke="{PRIMARY}" stroke-width="1.4"/>'
    )
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" '
        f'y2="{pad_t + plot_h}" stroke="{PRIMARY}" stroke-width="1.4"/>'
    )

    # Series (linea + puntos) con desplazamiento pseudo-3D en X.
    for index, serie in enumerate(series):
        color = PALETTE[index % len(PALETTE)]
        dx = float(serie.get("z") or 0) * DEPTH * plot_w
        coords = " ".join(
            f"{x_at(float(p[0])) + dx:.2f},{y_at(float(p[1])):.2f}"
            for p in (serie.get("points") or [])
            if len(p) >= 2 and p[0] is not None and p[1] is not None
        )
        if not coords:
            continue
        if coords.count(" ") >= 1:
            parts.append(
                f'<polyline points="{coords}" fill="none" stroke="{color}" '
                f'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        for point in serie.get("points") or []:
            if len(point) < 2 or point[0] is None or point[1] is None:
                continue
            parts.append(
                f'<circle cx="{x_at(float(point[0])) + dx:.2f}" '
                f'cy="{y_at(float(point[1])):.2f}" r="3.4" '
                f'fill="#ffffff" stroke="{color}" stroke-width="2"/>'
            )

    # Leyenda (solo si hay mas de una serie).
    if len([s for s in series if s.get("points")]) > 1:
        ly = pad_t + 4
        for index, serie in enumerate(series):
            if not serie.get("points"):
                continue
            color = PALETTE[index % len(PALETTE)]
            parts.append(
                f'<line x1="{pad_l + 8}" y1="{ly}" x2="{pad_l + 28}" y2="{ly}" '
                f'stroke="{color}" stroke-width="2.4"/>'
            )
            parts.append(
                f'<text x="{pad_l + 34}" y="{ly + 4}" fill="{MUTED}" '
                f'font-size="10">{escape(str(serie.get("name", "")))}</text>'
            )
            ly += 16

    # Titulos de ejes.
    if x_title:
        parts.append(
            f'<text x="{pad_l + plot_w / 2:.2f}" y="{height - 8}" '
            f'text-anchor="middle" fill="{PRIMARY}" font-size="11.5" '
            f'font-weight="600">{escape(str(x_title))}</text>'
        )
    if y_title:
        cx, cy = 16, pad_t + plot_h / 2
        parts.append(
            f'<text x="{cx}" y="{cy}" text-anchor="middle" fill="{PRIMARY}" '
            f'font-size="11.5" font-weight="600" '
            f'transform="rotate(-90 {cx} {cy})">{escape(str(y_title))}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
