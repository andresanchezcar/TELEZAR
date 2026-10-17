"""Graficas 3D de lineas (Calibracion distancia y atenuaciones) con matplotlib.

A partir del mismo diccionario ``chart`` que usa ``app/chart.py``:

    {"series": [{"name": "Muestra 1", "points": [[x, y], ...]}, ...],
     "title": "...", "x_title": "...", "y_title": "...",
     "x_ticks": [...], "x_tick_labels": [...]}

Se dibuja una linea por muestra a lo largo del eje Y (categorias discretas
``MUESTRA 1..5``). El eje X se trata de forma CATEGORICA: las posiciones son
indices secuenciales (0, 1, 2, ...) en el orden de la tabla, y las etiquetas de
las marcas son los valores reales formateados. El eje Z es el valor medido.

Se devuelve SVG (para la web, nitido) o PNG (para incrustar en el PDF). El
resultado se cachea en disco para no invocar matplotlib en cada peticion.

El formato reserva un margen derecho para la leyenda (para que no se monte
sobre la etiqueta del eje Y) y anade un margen de impresion (``pad_inches``)
para que nada se desborde al imprimir.
"""
import base64
import hashlib
import io
import json
import math
import os
import threading

PALETTE = ["#0a8fb0", "#e52421", "#2f8f5b", "#b8962f", "#7a4fd0", "#e07b00"]
PRIMARY = "#0c1c46"
MUTED = "#5b6b83"

# Subir cuando cambie el estilo/vista para invalidar la cache en disco.
RENDER_VERSION = 6

# Camara: inclinacion frontal, lateral y baja (identica para ambas graficas).
VIEW_ELEV = 18
VIEW_AZIM = -72

# Margen de impresion (pulgadas) alrededor de la figura.
PRINT_PAD = 0.25

# Configuracion por tipo de grafica.
KIND_CONFIG = {
    "distance": {
        "y_positions": [0.1, 0.2, 0.3, 0.4, 0.5],
        "box_aspect": (1.7, 1.1, 1.0),
        "fan_strength": 1.2,
        "title": "CALIBRACIÓN DISTANCIA",
        "z_mode": "fixed",
        "z_default": (0.0, 25.0, 5.0),
        "z_decimals": 0,
    },
    "attenuation": {
        "y_positions": [1.0, 1.15, 1.3, 1.45, 1.6],
        "box_aspect": (1.4, 0.45, 0.85),
        "fan_strength": 0.0,
        "title": "CALIBRACIÓN ATENUACIONES",
        "z_mode": "auto",
        "z_default": (0.0, 0.4, 0.1),
        "z_decimals": 3,
    },
}

_lock = threading.Lock()
_available = None


def available():
    """Indica si matplotlib esta instalado (se evalua una sola vez)."""
    global _available
    if _available is None:
        try:
            import matplotlib  # noqa: F401

            _available = True
        except Exception:
            _available = False
    return _available


def _comma(text):
    """Formatea con coma decimal (estilo de la tabla)."""
    return str(text).replace(".", ",")


def _chart_key(chart, kind, fmt, dpi):
    payload = json.dumps(chart, sort_keys=True, default=str)
    raw = (payload + f"|{kind}|{fmt}|{dpi}|v{RENDER_VERSION}").encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _cache_path(key, kind, fmt):
    try:
        from flask import current_app

        base = os.path.join(current_app.instance_path, "chart_cache")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"{kind}_{key}.{fmt}")
    except Exception:
        return None


def _valid(data, fmt):
    """Comprueba que el contenido de cache no este corrupto/truncado."""
    if not data:
        return False
    if fmt == "png":
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    if fmt == "svg":
        return b"<svg" in data[:2048]
    if fmt == "pdf":
        return data[:5] == b"%PDF-"
    return True


def render(chart, kind="distance", fmt="png", dpi=150):
    """Renderiza la grafica 3D. Devuelve bytes o ``None``."""
    if not isinstance(chart, dict):
        return None
    series = [s for s in (chart.get("series") or []) if s.get("points")]
    if not series or not available():
        return None

    key = _chart_key(chart, kind, fmt, dpi)
    path = _cache_path(key, kind, fmt)
    if path and os.path.isfile(path):
        try:
            with open(path, "rb") as fh:
                cached = fh.read()
            if _valid(cached, fmt):
                return cached
        except OSError:
            pass

    try:
        data = _build(chart, series, kind, fmt, dpi)
    except Exception:
        return None

    if data and path:
        try:
            # Escritura atomica: se evita que otra peticion lea a medias el
            # archivo (lo que produciria una imagen corrupta/ausente).
            tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, path)
        except OSError:
            pass
    return data


def _z_axis(cfg, values):
    """Devuelve (lo, hi, step) para el eje Z (valores de la medicion)."""
    lo, hi, step = cfg["z_default"]
    if cfg.get("z_mode") == "fixed":
        return lo, hi, step
    # Modo auto: de 0 hasta el maximo redondeado al siguiente multiplo de step.
    if values:
        hi = math.ceil(max(values) / step) * step
    hi = max(hi, step)
    return lo, round(hi, 10), step


def _build(chart, series, kind, fmt, dpi):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    cfg = KIND_CONFIG.get(kind, KIND_CONFIG["distance"])
    labels = [
        str(s.get("name") or f"Muestra {i + 1}").upper()
        for i, s in enumerate(series)
    ]

    # Eje X categorico: indice secuencial segun el orden de la tabla.
    x_ticks = chart.get("x_ticks") or []
    x_tick_labels = chart.get("x_tick_labels") or []
    index_of = {}
    for i, value in enumerate(x_ticks):
        try:
            index_of[round(float(value), 9)] = i
        except (TypeError, ValueError):
            continue
    n_x = len(x_ticks)

    with _lock:
        fig = plt.figure(figsize=(9.8, 5.4), dpi=dpi)
        # Se reserva el margen derecho para la leyenda (no se monta sobre el
        # eje Y) y un margen superior para el titulo.
        ax = fig.add_axes([0.02, 0.04, 0.62, 0.86], projection="3d")

        def x_pos(px):
            """Posicion categorica (indice) del patron px."""
            if index_of:
                idx = index_of.get(round(float(px), 9))
                if idx is not None:
                    return idx
            return float(px)

        datos = []
        z_values = []
        for index, serie in enumerate(series):
            puntos = [
                (float(p[0]), float(p[1]))
                for p in (serie.get("points") or [])
                if p and len(p) >= 2 and p[0] is not None and p[1] is not None
            ]
            if not puntos:
                continue
            datos.append((index, puntos))
            for _, py in puntos:
                z_values.append(py)

        y_positions = cfg["y_positions"]
        y_pos = [
            y_positions[index] if index < len(y_positions)
            else round(y_positions[0] + 0.15 * index, 2)
            for index, _ in datos
        ]

        # Desplazamiento SOLO visual por muestra para el efecto de abanico
        # (los valores de la tabla no se modifican). Solo aplica si
        # ``fan_strength`` > 0.
        centro = (len(datos) - 1) / 2.0
        fan = cfg["fan_strength"]
        handles = []
        for pos, (index, puntos) in enumerate(datos):
            color = PALETTE[index % len(PALETTE)]
            xs = [x_pos(p[0]) for p in puntos]
            zs = [p[1] for p in puntos]
            if fan and n_x > 1:
                gx = [x / (n_x - 1) for x in xs]
                zs = [
                    z + (index - centro) * fan * g for z, g in zip(zs, gx)
                ]
            ys = [y_pos[pos]] * len(xs)
            ax.plot(
                xs, ys, zs,
                color=color, linewidth=1.6, markersize=0,
                solid_capstyle="round",
            )
            handles.append(
                Patch(facecolor=color, edgecolor="none", label=labels[index])
            )

        # Etiquetas de ejes.
        ax.set_xlabel(chart.get("x_title") or "PATRONES", labelpad=12,
                      fontsize=9, color=PRIMARY)
        ax.set_ylabel("MUESTRAS", labelpad=12, fontsize=9, color=PRIMARY)
        ax.set_zlabel(chart.get("y_title") or "", labelpad=8,
                      fontsize=9, color=PRIMARY)

        # Eje Y (MUESTRAS) compacto, en orden 1..5.
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8, color=MUTED)
        dy = (y_pos[1] - y_pos[0]) if len(y_pos) > 1 else 0.05
        ax.set_ylim(min(y_pos) - dy * 0.5, max(y_pos) + dy * 0.5)

        # Eje Z (valor medido).
        zlo, zhi, zstep = _z_axis(cfg, z_values)
        ax.set_zlim(zlo, zhi)
        nticks = int(round((zhi - zlo) / zstep)) if zstep else 0
        if 0 < nticks <= 12:
            dec = cfg["z_decimals"]
            zticks = [round(zlo + i * zstep, 10) for i in range(nticks + 1)]
            ax.set_zticks(zticks)
            ax.set_zticklabels([_comma(f"{t:.{dec}f}") for t in zticks],
                               fontsize=7)

        # Eje X categorico: marcas secuenciales 0..n-1 con etiquetas reales.
        if n_x:
            ax.set_xticks(range(n_x))
            if len(x_tick_labels) == n_x:
                ax.set_xticklabels([_comma(t) for t in x_tick_labels],
                                   fontsize=7)
            ax.set_xlim(-0.4, n_x - 0.6)
        ax.tick_params(axis="x", labelsize=7, colors=MUTED)
        ax.tick_params(axis="z", labelsize=7, colors=MUTED)
        ax.tick_params(axis="y", labelsize=8, colors=MUTED)

        # Grilla 3D sutil.
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
            axis.pane.set_edgecolor("#e3e9f2")
        ax.grid(True)

        ax.set_box_aspect(cfg["box_aspect"])
        ax.view_init(elev=VIEW_ELEV, azim=VIEW_AZIM)

        title = chart.get("title") or cfg["title"]
        ax.set_title(title, fontsize=12, fontweight="bold", color=PRIMARY, pad=12)

        # Leyenda vertical a la derecha, con cajas cuadradas (sin lineas),
        # fuera del area de ejes para no montarse sobre la etiqueta del eje Y.
        fig.legend(handles=handles, loc="center left",
                   bbox_to_anchor=(0.70, 0.5), fontsize=9, frameon=False,
                   handlelength=1.1, handleheight=1.1, borderpad=0.4,
                   labelspacing=0.6)

        buf = io.BytesIO()
        fig.savefig(buf, format=fmt, dpi=dpi, facecolor="white",
                    bbox_inches="tight", pad_inches=PRINT_PAD)
        plt.close(fig)

    return buf.getvalue()


def _data_uri(chart, kind, fmt):
    data = render(chart, kind=kind, fmt=fmt)
    if not data:
        return None
    mime = "image/svg+xml" if fmt == "svg" else "image/png"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def distance_data_uri(chart, fmt="svg"):
    """Data URI de la grafica 3D de distancia (o ``None``)."""
    return _data_uri(chart, "distance", fmt)


def attenuation_data_uri(chart, fmt="svg"):
    """Data URI de la grafica 3D de atenuaciones (o ``None``)."""
    return _data_uri(chart, "attenuation", fmt)


def distance_png(chart):
    """Bytes PNG de la grafica 3D de distancia (para el PDF) o ``None``."""
    return render(chart, kind="distance", fmt="png", dpi=160)


def attenuation_png(chart):
    """Bytes PNG de la grafica 3D de atenuaciones (para el PDF) o ``None``."""
    return render(chart, kind="attenuation", fmt="png", dpi=160)
