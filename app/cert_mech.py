"""Datos del certificado de AJUSTE Y CALIBRACION MECANICA (JSON en mech_data).

Estructura del JSON:
    {
        "legal": "texto de certificacion",
        "actions": ["Ajuste de sensores", ...],
        "patrones": [{"descripcion","fabricante","modelo","serie","certificado","vence"}],
        "environment": {"temp","temp_tol","humidity","humidity_tol"}
    }
"""
import json

DEFAULT_LEGAL = (
    "TELEZAR COMUNICACIONES. Certifica que la máquina de Empalme por Fusión "
    "realizada a continuación, se encuentra fusionando normalmente y cumple con "
    "las especificaciones de exactitud de medida, ha sido ajustada mecánicamente "
    "en los siguientes parámetros para fusiones en fibra Óptica Monomodo y "
    "Multimodo, siguiendo los parámetros recomendados por el fabricante."
)

DEFAULT_ACTIONS = [
    "Ajuste de sensores",
    "Mantenimiento y limpieza de camber, espejos, pisa fibras y cuerpo de equilibrio del equipo",
    "Ajustes de motores y carros",
    "Limpieza de V-Grooves",
    "Ajuste de función de corrección de excentricidad",
    "Ajuste posición de arco",
    "Ajuste de Fiber Clamp",
]

PATRON_KEYS = ("descripcion", "fabricante", "modelo", "serie", "certificado", "vence")
ENV_KEYS = ("temp", "temp_tol", "humidity", "humidity_tol")


def _s(value):
    return str(value).strip() if value is not None else ""


def _empty_env():
    return {key: "" for key in ENV_KEYS}


def parse_mech(raw):
    """Convierte el JSON almacenado en un dict normalizado (sin filas vacias)."""
    data = {"legal": "", "actions": [], "patrones": [], "environment": _empty_env()}
    text = _s(raw)
    if not text:
        return data
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return data
    if not isinstance(obj, dict):
        return data

    data["legal"] = _s(obj.get("legal"))

    for action in obj.get("actions") or []:
        value = _s(action)
        if value:
            data["actions"].append(value)

    for row in obj.get("patrones") or []:
        if not isinstance(row, dict):
            continue
        parsed = {key: _s(row.get(key)) for key in PATRON_KEYS}
        if any(parsed.values()):
            data["patrones"].append(parsed)

    env = obj.get("environment") if isinstance(obj.get("environment"), dict) else {}
    for key in ENV_KEYS:
        data["environment"][key] = _s(env.get(key))

    return data


def serialize_mech(raw):
    """Normaliza y devuelve el JSON a guardar (o "" si no hay nada)."""
    data = parse_mech(raw)
    has_env = any(data["environment"].values())
    if not any((data["legal"], data["actions"], data["patrones"])) and not has_env:
        return ""
    return json.dumps(data, ensure_ascii=False)


def _env_parts(env):
    """Pares etiqueta/valor de las condiciones ambientales (estilo OTDR)."""
    parts = []
    if env.get("temp"):
        value = env["temp"] + (" ± " + env["temp_tol"] if env.get("temp_tol") else "")
        parts.append(("Temperatura ambiente media", value + " °C"))
    if env.get("humidity"):
        value = env["humidity"] + (
            " ± " + env["humidity_tol"] if env.get("humidity_tol") else ""
        )
        parts.append(("Humedad relativa", value + " %"))
    return parts


def build_mech_view(raw):
    """Vista para plantillas/PDF. Si aun no se ha configurado, usa los valores por defecto."""
    configured = bool(_s(raw))
    data = parse_mech(raw)
    if not configured:
        data["legal"] = DEFAULT_LEGAL
        data["actions"] = list(DEFAULT_ACTIONS)
    data["env_parts"] = _env_parts(data["environment"])
    return data


def patrones_source(certificates):
    """Mapa {serie -> datos} de los equipos ya certificados para autocompletar."""
    source = {}
    for cert in certificates:
        serial = _s(getattr(cert, "serial", ""))
        if not serial:
            continue
        key = serial.upper()
        if key in source:
            continue
        source[key] = {
            "descripcion": _s(getattr(cert, "equipment", "")) or _s(getattr(cert, "device_label", "")),
            "fabricante": _s(getattr(cert, "equipment_brand", "")),
            "modelo": _s(getattr(cert, "equipment_model", "")),
            "certificado": _s(getattr(cert, "code", "")),
            "vence": cert.next_date.strftime("%d/%m/%Y") if getattr(cert, "next_date", None) else "",
        }
    return source
