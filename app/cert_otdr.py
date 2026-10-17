"""Datos, estadisticas y vista del certificado OTDR.

El certificado OTDR guarda toda su informacion estructurada (condiciones de la
calibracion, calibraciones de distancia, calibraciones de atenuacion, patrones y
metodos utilizados) como un JSON en la columna ``Certificate.otdr_data``.

Aqui se centraliza:
  * el parseo/normalizacion robusto de ese JSON,
  * el calculo del promedio y la desviacion estandar (muestral, n-1),
  * la construccion de una "vista" lista para plantillas y para el PDF.
"""
import json
import math

DEFAULT_SAMPLES = 5

# Texto legal que aparece centrado antes de la firma.
OTDR_LEGEND = (
    "El presente documento certifica que el equipo de la referencia se encuentra "
    "trabajando normalmente y que cumple con las especificaciones de exactitud de "
    "medida indicados por el fabricante. Los parámetros mencionados han sido "
    "comprobados siguiendo los procedimientos especificados por el fabricante y "
    "proporcionan un nivel de confiabilidad del 95% usando K=2 y siguiendo los "
    "lineamientos de la NTC 2194; los instrumentos utilizados para esta calibración "
    "se encuentran trazados al patrón internacional de medición NIST (National "
    "Institute of Standards and Technology)."
)


# --------------------------------------------------------------------------
# Numeros
# --------------------------------------------------------------------------
def to_float(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value, decimals=3):
    num = to_float(value)
    if num is None:
        return ""
    return f"{num:.{decimals}f}"


def mean(values):
    nums = [n for n in (to_float(v) for v in values) if n is not None]
    return sum(nums) / len(nums) if nums else None


def stdev(values):
    """Desviacion estandar muestral (divide entre n-1)."""
    nums = [n for n in (to_float(v) for v in values) if n is not None]
    if len(nums) < 2:
        return None
    m = sum(nums) / len(nums)
    variance = sum((x - m) ** 2 for x in nums) / (len(nums) - 1)
    return variance ** 0.5


# --------------------------------------------------------------------------
# Escalas de eje ("nice numbers") para las graficas
# --------------------------------------------------------------------------
def _nice_step(span, count):
    if span <= 0:
        return 1.0
    raw = span / count
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiplier in (1, 2, 2.5, 5, 10):
        if raw <= multiplier * magnitude:
            return multiplier * magnitude
    return 10 * magnitude


def nice_bounds(lo, hi, count=5, zero=False):
    """Devuelve [min, max, paso] con valores "redondos" que cubren [lo, hi]."""
    if lo is None or hi is None:
        return None
    lo = float(lo)
    hi = float(hi)
    if zero:
        lo = min(lo, 0.0)
    if hi <= lo:
        hi = lo + (abs(lo) or 1.0)
    step = _nice_step(hi - lo, count)
    nmin = math.floor(lo / step) * step
    nmax = math.ceil(hi / step) * step
    return [round(nmin, 10), round(nmax, 10), round(step, 10)]


def _axis_values(bounds):
    if not bounds:
        return []
    lo, hi, step = bounds
    ticks = []
    value = lo
    guard = 0
    while value <= hi + step / 1000 and guard < 1000:
        ticks.append(round(value, 10))
        value += step
        guard += 1
    return ticks


def _sample_series(xs, rows, sample_count=DEFAULT_SAMPLES):
    """Una serie por muestra.

    Cada serie recibe un valor ``z`` equilibrado alrededor de 0 para que los
    renderizadores puedan aplicar un pequeno desplazamiento horizontal
    (efecto pseudo-3D) y distinguir visualmente las muestras.
    """
    half = (sample_count - 1) / 2.0
    series = []
    for index in range(sample_count):
        points = []
        for x, row in zip(xs, rows):
            if x is None:
                continue
            samples = row.get("samples") or []
            value = to_float(samples[index]) if index < len(samples) else None
            if value is None:
                continue
            points.append([x, value])
        series.append({
            "name": f"Muestra {index + 1}",
            "points": points,
            "z": index - half,
        })
    return series


# --------------------------------------------------------------------------
# Normalizacion
# --------------------------------------------------------------------------
def _clean(value):
    return str(value if value is not None else "").strip()


def _clean_samples(samples, count=DEFAULT_SAMPLES):
    if not isinstance(samples, list):
        samples = []
    return [_clean(samples[i]) if i < len(samples) else "" for i in range(count)]


def _clean_list(items):
    if not isinstance(items, list):
        return []
    return [_clean(i) for i in items if _clean(i)]


def _normalize_distance(items):
    result = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        rows = []
        for row in item.get("rows") or []:
            if not isinstance(row, dict):
                continue
            initial = _clean(row.get("initial"))
            samples = _clean_samples(row.get("samples"))
            if not initial and not any(samples):
                # Fila vacía (sin valor inicial ni muestras): se descarta.
                continue
            rows.append({
                "pattern": str(len(rows) + 1),
                "initial": initial,
                "samples": samples,
            })
        if not rows:
            # Calibración sin filas útiles: se descarta.
            continue
        result.append({"wavelength": _clean(item.get("wavelength")), "rows": rows})
    return result


def _normalize_attenuation(items):
    result = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        rows = []
        for row in item.get("rows") or []:
            if not isinstance(row, dict):
                continue
            pattern = _clean(row.get("pattern"))
            samples = _clean_samples(row.get("samples"))
            if not pattern and not any(samples):
                # Fila vacía (sin valor patrón ni muestras): se descarta.
                continue
            rows.append({
                "event": str(len(rows) + 1),
                "pattern": pattern,
                "samples": samples,
            })
        if not rows:
            # Calibración sin filas útiles: se descarta.
            continue
        result.append({"wavelength": _clean(item.get("wavelength")), "rows": rows})
    return result


def parse_otdr(raw):
    data = {}
    if raw:
        try:
            data = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (ValueError, TypeError):
            data = {}
    if not isinstance(data, dict):
        data = {}
    env = data.get("environment") if isinstance(data.get("environment"), dict) else {}
    return {
        "environment": {
            "temp": _clean(env.get("temp")),
            "temp_tol": _clean(env.get("temp_tol")),
            "humidity": _clean(env.get("humidity")),
            "humidity_tol": _clean(env.get("humidity_tol")),
        },
        "distance": _normalize_distance(data.get("distance")),
        "attenuation": _normalize_attenuation(data.get("attenuation")),
        "patterns": _clean_list(data.get("patterns")),
        "methods": _clean_list(data.get("methods")),
    }


def serialize_otdr(data):
    if not isinstance(data, dict):
        return ""
    return json.dumps(data, ensure_ascii=False)


# --------------------------------------------------------------------------
# Vista lista para plantillas / PDF
# --------------------------------------------------------------------------
def _row_view(base, samples):
    mean_v = mean(samples)
    std_v = stdev(samples)
    view = dict(base)
    view.update({
        "samples": samples,
        "mean": fmt(mean_v, 4),
        "stdev": fmt(std_v, 9),
        "mean_value": mean_v,
        "stdev_value": std_v,
    })
    return view


def build_otdr_view(raw):
    data = parse_otdr(raw)
    env = data["environment"]

    env_parts = []
    if env["temp"]:
        value = env["temp"] + (" ± " + env["temp_tol"] if env["temp_tol"] else "")
        env_parts.append(("Temperatura ambiente media", value + " °C"))
    if env["humidity"]:
        value = env["humidity"] + (" ± " + env["humidity_tol"] if env["humidity_tol"] else "")
        env_parts.append(("Humedad relativa", value + " %"))

    distance = []
    for cal in data["distance"]:
        rows = [_row_view(
            {"pattern": r["pattern"], "initial": r["initial"]}, r["samples"]
        ) for r in cal["rows"]]

        x_ticks = []
        for index, row in enumerate(rows):
            xv = to_float(row["initial"])
            if xv is None:
                xv = to_float(row["pattern"])
            if xv is None:
                xv = float(index + 1)
            x_ticks.append(xv)

        series = _sample_series(x_ticks, rows)
        values = [
            value for row in rows
            for value in (to_float(s) for s in row["samples"]) if value is not None
        ]
        y_axis = nice_bounds(min(values), max(values)) if values else None

        distance.append({
            "wavelength": cal["wavelength"],
            "rows": rows,
            "x_title": "PATRONES",
            "y_title": "DISTANCIA (KM)",
            "chart": {
                "series": series,
                "title": "CALIBRACIÓN DISTANCIA",
                "x_title": "PATRONES",
                "y_title": "DISTANCIA (KM)",
                "x_axis": None,
                "y_axis": y_axis,
                "x_ticks": x_ticks,
                "x_tick_labels": [fmt(x, 3) for x in x_ticks],
            },
        })

    attenuation = []
    for cal in data["attenuation"]:
        rows = [_row_view(
            {"event": r["event"], "pattern": r["pattern"]}, r["samples"]
        ) for r in cal["rows"]]

        x_ticks = [to_float(r["pattern"]) for r in rows]
        pattern_values = [x for x in x_ticks if x is not None]
        series = _sample_series(x_ticks, rows)

        if pattern_values:
            y_axis = nice_bounds(0.0, max(pattern_values), zero=True)
        else:
            values = [
                value for row in rows
                for value in (to_float(s) for s in row["samples"]) if value is not None
            ]
            y_axis = nice_bounds(0.0, max(values), zero=True) if values else None

        attenuation.append({
            "wavelength": cal["wavelength"],
            "rows": rows,
            "x_title": "ATENUACIONES PATRÓN",
            "y_title": "Atenuación (dB)",
            "chart": {
                "series": series,
                "title": "CALIBRACIÓN ATENUACIONES"
                         + (f" {cal['wavelength']}" if cal.get("wavelength") else ""),
                "x_title": "ATENUACIONES PATRÓN",
                "y_title": "Atenuación (dB)",
                "x_axis": None,
                "y_axis": y_axis,
                "y_tick_labels": [f"{t:.3f}" for t in _axis_values(y_axis)] if y_axis else None,
                "x_ticks": pattern_values,
                "x_tick_labels": [fmt(x, 3) for x in pattern_values],
            },
        })

    return {
        "environment": env,
        "env_parts": env_parts,
        "distance": distance,
        "attenuation": attenuation,
        "patterns": data["patterns"],
        "methods": data["methods"],
        "legend": OTDR_LEGEND,
        "has_data": bool(
            env_parts or distance or attenuation or data["patterns"] or data["methods"]
        ),
    }
