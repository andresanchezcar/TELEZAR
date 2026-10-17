import os

from flask import current_app, flash, redirect, request, url_for
from werkzeug.utils import secure_filename

from app.models import Brand, Category, Page, Service, Setting
from app.extensions import db


def get_base_url(settings=None):
    """Dominio base: ajuste `site_url` (panel admin) -> config SITE_URL -> host de la peticion."""
    if settings:
        domain = (settings.get("site_url") or "").strip().rstrip("/")
        if domain:
            return domain
    configured = (current_app.config.get("SITE_URL") or "").rstrip("/")
    return configured or request.url_root.rstrip("/")


def absolute_url(path):
    if not path:
        return ""
    if path.startswith(("http://", "https://", "//")):
        return path
    return get_base_url() + path


def allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(file_storage, subdir=""):
    """Guarda un archivo subido y devuelve la ruta relativa /uploads/..."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        flash("Tipo de archivo no permitido.", "error")
        return None

    from app.models import new_uuid_name

    filename = new_uuid_name(secure_filename(file_storage.filename))
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"/uploads/{subdir + '/' if subdir else ''}{filename}"


def delete_upload(path):
    """Elimina un archivo previamente subido (best effort)."""
    if not path or not path.startswith("/uploads/"):
        return
    full = os.path.join(current_app.config["UPLOAD_FOLDER"], path[len("/uploads/") :])
    try:
        if os.path.isfile(full):
            os.remove(full)
    except OSError:
        pass


def upload_abspath(path):
    """Convierte una ruta /uploads/... en su ruta absoluta en disco."""
    if not path or not path.startswith("/uploads/"):
        return None
    full = os.path.join(current_app.config["UPLOAD_FOLDER"], path[len("/uploads/") :])
    return full if os.path.isfile(full) else None


def get_settings():
    return {s.key: s.value for s in Setting.query.all()}


def company_logo_path():
    """Ruta absoluta del logo configurado (o el logo por defecto) para el QR."""
    logo = (Setting.get("site_logo", "") or "").strip()
    candidates = []
    if logo.startswith("/uploads/"):
        candidates.append(
            os.path.join(current_app.config["UPLOAD_FOLDER"], logo[len("/uploads/") :])
        )
    elif logo.startswith("/static/"):
        candidates.append(
            os.path.join(current_app.root_path, logo[len("/static/") :])
        )
    candidates.append(os.path.join(current_app.root_path, "static", "img", "logo.png"))
    for path in candidates:
        try:
            if path and os.path.isfile(path):
                return path
        except OSError:
            continue
    return None


SETTINGS_SECTION_ORDER = [
    "Identidad",
    "SEO",
    "Hero (Inicio)",
    "Video (Inicio)",
    "Sobre nosotros",
    "Mision / Vision / Garantia",
    "Contacto",
    "Redes sociales",
    "Catalogo",
    "Certificados",
    "Pie de pagina",
]

SETTINGS_KEY_ORDER = [
    "site_name", "site_tagline", "site_logo", "favicon",
    "company_nit", "company_legal_rep",
    "site_url", "seo_keywords", "og_image",
    "hero_badge", "hero_title", "hero_subtitle", "hero_image",
    "home_video",
    "about_title", "about_text", "about_image", "about_badge_number", "about_badge_text",
    "mission", "vision", "guarantee",
    "phone", "phone2", "whatsapp", "address", "schedule",
    "email_general", "email_ventas", "email_soporte", "email_infosoporte",
    "facebook", "twitter", "linkedin", "instagram",
    "catalog_text_venta", "catalog_text_alquiler",
    "cert_title", "cert_text",
    "footer_text", "copyright",
]


def _order_rank(values, item):
    try:
        return values.index(item)
    except ValueError:
        return len(values)


def get_settings_by_section():
    """Agrupa los ajustes por seccion en un orden logico (no alfabetico)."""
    rows = Setting.query.all()
    rows.sort(
        key=lambda s: (
            _order_rank(SETTINGS_SECTION_ORDER, s.section),
            s.section,
            _order_rank(SETTINGS_KEY_ORDER, s.key),
            s.key,
        )
    )
    sections = {}
    for s in rows:
        sections.setdefault(s.section, []).append(s)
    return sections


DEFAULT_LABELS = {
    # Navegacion
    "nav_inicio": "Inicio",
    "nav_nosotros": "Nosotros",
    "nav_servicios": "Servicios",
    "nav_servicios_todos": "Todos los servicios",
    "nav_ventas": "Ventas",
    "nav_alquiler": "Alquiler de equipos",
    "nav_capacitaciones": "Capacitaciones y entrenamiento",
    "nav_soporte": "Centro de soporte tecnico",
    "nav_certificados": "Certificados",
    "nav_contacto": "Contacto",
    "nav_ingresar": "Ingresar",
    "nav_cotizar": "Cotizar",
    # Footer
    "footer_menu": "Menu",
    "footer_servicios": "Servicios",
    "footer_contactanos": "Contactanos",
    "footer_administracion": "Administracion",
    # Hero (inicio)
    "hero_contactanos": "Contactanos",
    "hero_ver_servicios": "Ver servicios",
    "hero_highlight_1": "Atencion 24/7",
    "hero_highlight_2": "Equipos calibrados",
    "hero_highlight_3": "Personal certificado",
    # Seccion video (inicio)
    "sec_video_eyebrow": "Conozcanos",
    "sec_video_title": "Nuestro trabajo en accion",
    "sec_video_text": "Un recorrido por los servicios, el laboratorio y el equipo humano de TELEZAR COMUNICACIONES.",
    # Seccion servicios (inicio)
    "sec_servicios_eyebrow": "Lo que hacemos",
    "sec_servicios_title": "Nuestros servicios",
    "sec_servicios_text": "Soluciones integrales en redes, fibra optica y telecomunicaciones para su empresa.",
    "link_ver_mas": "Ver mas",
    # Seccion nosotros (inicio)
    "sec_nosotros_eyebrow": "Sobre nosotros",
    "btn_conocenos": "Conocenos",
    # Seccion galeria (inicio)
    "sec_galeria_eyebrow": "Nuestros trabajos",
    "sec_galeria_title": "Galeria de proyectos",
    "sec_galeria_text": "El equipo humano y tecnico que garantiza la calidad de nuestro trabajo.",
    # Seccion marcas (inicio)
    "sec_marcas_eyebrow": "Alianzas",
    "sec_marcas_title": "Trabajamos con las mejores marcas del sector",
    # CTA certificados
    "btn_busca_certificado": "Busca tu certificado",
    # Valores
    "value_mission": "Misión",
    "value_vision": "Visión",
    "value_guarantee": "Garantia",
    # Bloque CTA general
    "cta_pregunta": "¿Necesita mas informacion?",
    "cta_contado": "Nuestro equipo esta listo para atender sus solicitudes.",
    "btn_escribenos": "Escribenos",
    # Breadcrumbs y paginacion
    "bread_inicio": "Inicio",
    "bread_servicios": "Servicios",
    "bread_contacto": "Contacto",
    "bread_certificados": "Certificados",
    "bread_catalogo": "Catalogo",
    "paginacion_anterior": "Anterior",
    "paginacion_siguiente": "Siguiente",
    # Pagina de servicios
    "servicios_title": "Nuestros servicios",
    "servicios_intro": "Contamos con el equipo humano y tecnico que su compania necesita para acceder a lo ultimo de la tecnologia en instalacion, mantenimiento, soporte, certificacion y calibracion.",
    "servicios_empty": "Aun no hay servicios publicados.",
    "btn_contactanos": "Contactanos",
    # Catalogo (ventas / alquiler)
    "catalogo_venta": "Venta de equipos",
    "catalogo_alquiler": "Alquiler de equipos",
    "catalogo_buscar": "Buscar equipo o herramienta...",
    "catalogo_todos": "Todos",
    "catalogo_limpiar": "Limpiar filtros",
    "catalogo_empty": "No se encontraron productos con los filtros seleccionados.",
    # Detalle de producto
    "producto_disponibilidad": "Disponibilidad:",
    "producto_precio": "Precio:",
    "producto_consulte_wa": "Consulte por WhatsApp",
    "producto_consultar_wa": "Consultar por WhatsApp",
    "producto_venta": "Venta",
    "producto_alquiler": "Alquiler",
    "producto_vapor": "Venta y alquiler",
    "producto_volver": "Volver al catalogo",
    "producto_descripcion": "Descripcion",
    # Certificados
    "cert_buscar": "Buscar",
    "cert_placeholder": "Ej. TZC0738, 27AM1701, numero de certificado...",
    "cert_cliente": "Cliente:",
    "cert_equipo": "Equipo:",
    "cert_emitido": "Emitido:",
    "cert_descargar": "Descargar PDF",
    "cert_empty": "No encontramos certificados para «{q}». Verifique el numero de serie o contactenos.",
    "cert_help_title": "¿Donde encuentro el número de certificado?",
    "cert_help_text": "El numero de certificado se encuentra en la etiqueta de su equipo (fusionadora, OTDR, cortadora, etc.).",
    "cert_necesito_ayuda": "Necesito ayuda",
    "cert_ver": "Ver certificado",
    "cert_descargar_pdf": "Descargar PDF",
    "cert_pdf_adjunto": "PDF adjunto",
    "cert_imprimir": "Imprimir",
    "cert_vigente": "Certificado vigente",
    "cert_vencido": "Certificado vencido",
    "cert_revocado": "Certificado no disponible",
    "cert_verificar_titulo": "Verificación de certificado",
    "cert_verificar_texto": "Este certificado fue emitido por TELEZAR COMUNICACIONES. Escanee el código QR o consulte el número de serie para validar su autenticidad.",
    # Contacto
    "contacto_title": "Contacto",
    "contacto_intro": "Estamos listos para atender sus solicitudes. «Trabajamos con actitud positiva, compromiso y dedicacion para servirle siempre».",
    "contacto_escribenos": "Escribenos",
    "form_nombre": "Nombre",
    "form_telefono": "Telefono",
    "form_email": "Correo electronico",
    "form_asunto": "Asunto",
    "form_mensaje": "Mensaje",
    "contacto_enviar": "Enviar mensaje",
    "contacto_directo": "Directo con nosotros",
    "contacto_chat_wa": "Chatear por WhatsApp",
    "contacto_otras_opciones": "Otras opciones",
    # Paginas de error
    "error_volver_inicio": "Volver al inicio",
    "error_404_title": "La pagina que busca no existe",
    "error_404_text": "Puede que el enlace este roto o que la pagina haya sido movida.",
    "error_500_title": "Ocurrio un problema inesperado",
    "error_500_text": "Nuestro equipo ya fue notificado. Intentelo de nuevo en unos minutos.",
}


def get_labels(settings):
    """Etiquetas de interfaz: defaults + override guardados como 'label_<clave>'."""
    labels = dict(DEFAULT_LABELS)
    for key, value in settings.items():
        if key.startswith("label_"):
            labels[key[len("label_") :]] = value
    return labels


def asset_version():
    """Version de los assets (CSS/JS) a partir de su fecha de modificacion.

    Se usa como query string (?v=...) para forzar al navegador a recargar los
    estilos y scripts cuando cambian, evitando que queden versiones en cache."""
    root = current_app.root_path
    latest = 0.0
    for rel in (
        "static/css/style.css",
        "static/css/admin.css",
        "static/js/main.js",
        "static/js/admin.js",
    ):
        path = os.path.join(root, *rel.split("/"))
        try:
            latest = max(latest, os.path.getmtime(path))
        except OSError:
            continue
    return str(int(latest)) if latest else "1"


def base_context():
    """Contexto comun a todas las plantillas publicas."""
    settings = get_settings()
    pages = Page.query.filter_by(published=True).order_by(Page.order).all()
    base = get_base_url(settings)
    og_image = (
        settings.get("og_image")
        or settings.get("site_logo")
        or settings.get("favicon")
        or "/static/img/logo.png"
    )
    labels = get_labels(settings)

    def t(label_key, **kwargs):
        value = labels.get(label_key, label_key)
        for k, v in kwargs.items():
            value = value.replace("{" + k + "}", str(v))
        return value

    return {
        "settings": settings,
        "labels": labels,
        "t": t,
        "nav_pages": pages,
        "nav_services": Service.query.filter_by(published=True)
        .order_by(Service.order)
        .all(),
        "categories": Category.query.filter_by(published=True)
        .order_by(Category.order)
        .all(),
        "brands": Brand.query.filter_by(published=True).order_by(Brand.order).all(),
        "base_url": base,
        "current_url": request.url,
        "canonical_url": base + request.path,
        "og_image": absolute_url(og_image),
        "asset_v": asset_version(),
    }
