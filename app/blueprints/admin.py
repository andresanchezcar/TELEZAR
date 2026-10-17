import datetime
import re
from dataclasses import dataclass, field as dc_field
from typing import List, Optional

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Brand,
    Category,
    Certificate,
    CertificateTest,
    ContactMessage,
    GalleryImage,
    HomeModal,
    Page,
    Product,
    Service,
    Setting,
    Signature,
    User,
    new_cert_code,
    unique_slug,
)
from app.qr import qr_png
from app.utils import (
    DEFAULT_LABELS,
    company_logo_path,
    delete_upload,
    get_base_url,
    get_settings_by_section,
    save_upload,
)

admin_bp = Blueprint("admin", __name__)


# --------------------------------------------------------------------------
# Definicion de entidades administrables
# --------------------------------------------------------------------------
@dataclass
class Field:
    name: str
    label: str
    type: str = "text"  # text|textarea|slug|image|select|bool|number|price|date
    required: bool = False
    choices: List = dc_field(default_factory=list)
    choices_source: str = ""
    help: str = ""
    rows: int = 6
    default: str = ""
    show_if: Optional[dict] = None


@dataclass
class Entity:
    key: str
    label: str
    singular: str
    model: type
    fields: List[Field]
    columns: List[dict]
    order_by: str = "-id"
    image_fields: List[str] = dc_field(default_factory=list)


ENTITIES = {
    "paginas": Entity(
        key="paginas",
        label="Paginas",
        singular="pagina",
        model=Page,
        fields=[
            Field("title", "Titulo", required=True),
            Field("slug", "Slug (URL)", type="slug", help="Se genera automaticamente si se deja vacio"),
            Field("subtitle", "Subtitulo"),
            Field("body", "Contenido", type="textarea", rows=14),
            Field("image", "Imagen de cabecera", type="image"),
            Field("show_in_nav", "Mostrar en el menu", type="bool"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicada", type="bool"),
        ],
        columns=[
            {"name": "title", "label": "Titulo"},
            {"name": "slug", "label": "Slug"},
            {"name": "order", "label": "Orden", "type": "number"},
            {"name": "published", "label": "Publicada", "type": "bool"},
        ],
        order_by="order",
        image_fields=["image"],
    ),
    "servicios": Entity(
        key="servicios",
        label="Servicios",
        singular="servicio",
        model=Service,
        fields=[
            Field("title", "Titulo", required=True),
            Field(
                "icon",
                "Icono",
                type="select",
                choices=[
                    ("fiber", "Fibra optica"),
                    ("tools", "Herramientas / reparacion"),
                    ("cert", "Certificacion y calibracion"),
                    ("train", "Capacitacion"),
                    ("network", "Redes"),
                    ("support", "Soporte tecnico"),
                ],
            ),
            Field("excerpt", "Resumen", type="textarea", rows=3),
            Field("body", "Descripcion completa", type="textarea", rows=8),
            Field("image", "Imagen", type="image"),
            Field("featured", "Destacado en el inicio", type="bool"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicado", type="bool"),
        ],
        columns=[
            {"name": "title", "label": "Titulo"},
            {"name": "icon", "label": "Icono"},
            {"name": "featured", "label": "Destacado", "type": "bool"},
            {"name": "published", "label": "Publicado", "type": "bool"},
        ],
        order_by="order",
        image_fields=["image"],
    ),
    "categorias": Entity(
        key="categorias",
        label="Categorias",
        singular="categoria",
        model=Category,
        fields=[
            Field("name", "Nombre", required=True),
            Field("slug", "Slug (URL)", type="slug"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicada", type="bool"),
        ],
        columns=[
            {"name": "name", "label": "Nombre"},
            {"name": "slug", "label": "Slug"},
            {"name": "published", "label": "Publicada", "type": "bool"},
        ],
        order_by="order",
    ),
    "productos": Entity(
        key="productos",
        label="Productos",
        singular="producto",
        model=Product,
        fields=[
            Field("name", "Nombre", required=True),
            Field("slug", "Slug (URL)", type="slug"),
            Field("category_id", "Categoria", type="select", choices_source="categories"),
            Field(
                "availability",
                "Disponible para",
                type="select",
                choices=[
                    ("venta", "Venta"),
                    ("alquiler", "Alquiler"),
                    ("ambos", "Venta y alquiler"),
                ],
            ),
            Field("price", "Precio (COP, vacio = consultar)", type="price"),
            Field("summary", "Resumen", type="textarea", rows=3),
            Field("description", "Descripcion", type="textarea", rows=10),
            Field("image", "Imagen", type="image"),
            Field("featured", "Destacado", type="bool"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicado", type="bool"),
        ],
        columns=[
            {"name": "name", "label": "Nombre"},
            {"name": "availability", "label": "Disponible para"},
            {"name": "price", "label": "Precio", "type": "price"},
            {"name": "published", "label": "Publicado", "type": "bool"},
        ],
        order_by="-id",
        image_fields=["image"],
    ),
    "marcas": Entity(
        key="marcas",
        label="Marcas",
        singular="marca",
        model=Brand,
        fields=[
            Field("name", "Nombre", required=True),
            Field("logo", "Logo", type="image"),
            Field("url", "Sitio web", type="text"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicada", type="bool"),
        ],
        columns=[
            {"name": "name", "label": "Nombre"},
            {"name": "url", "label": "Sitio web"},
            {"name": "published", "label": "Publicada", "type": "bool"},
        ],
        order_by="order",
        image_fields=["logo"],
    ),
    "certificados": Entity(
        key="certificados",
        label="Certificados",
        singular="certificado",
        model=Certificate,
        fields=[
            Field("serial", "Numero de serie", required=True),
            Field("client", "Cliente"),
            Field("equipment", "Equipo"),
            Field("issued_date", "Fecha de emision", type="date"),
            Field("file_url", "Archivo PDF (subir)", type="image"),
            Field("notes", "Notas"),
            Field("published", "Publicado", type="bool"),
        ],
        columns=[
            {"name": "serial", "label": "Serie"},
            {"name": "code", "label": "Código"},
            {"name": "client", "label": "Cliente"},
            {"name": "equipment", "label": "Equipo"},
            {"name": "cert_type", "label": "Tipo", "choices": list(Certificate.TYPES.items())},
            {"name": "device_type", "label": "Dispositivo", "choices": list(Certificate.DEVICE_TYPES.items())},
            {"name": "doc_mode", "label": "Modo", "choices": list(Certificate.MODES.items())},
            {"name": "issued_date", "label": "Emitido", "type": "date"},
            {"name": "published", "label": "Publicado", "type": "bool"},
        ],
        order_by="-issued_date",
        image_fields=["file_url", "signature"],
    ),
    "galeria": Entity(
        key="galeria",
        label="Galeria",
        singular="imagen",
        model=GalleryImage,
        fields=[
            Field("title", "Titulo"),
            Field("image", "Imagen", type="image", required=True),
            Field("album", "Album"),
            Field("order", "Orden", type="number"),
            Field("published", "Publicada", type="bool"),
        ],
        columns=[
            {"name": "image", "label": "Imagen", "type": "image"},
            {"name": "title", "label": "Titulo"},
            {"name": "album", "label": "Album"},
            {"name": "published", "label": "Publicada", "type": "bool"},
        ],
        order_by="order",
        image_fields=["image"],
    ),
    "modales": Entity(
        key="modales",
        label="Modales del inicio",
        singular="modal",
        model=HomeModal,
        fields=[
            Field("title", "Titulo", required=True),
            Field("body", "Contenido", type="textarea", rows=6, help="Texto que se muestra en el modal."),
            Field("image", "Imagen", type="image", help="Opcional. Se muestra arriba del contenido."),
            Field(
                "button_action",
                "Acción",
                type="select",
                default="none",
                choices=[
                    ("none", "Sin botón"),
                    ("page", "Ir a una página del sitio"),
                    ("url", "Abrir un enlace externo"),
                    ("whatsapp", "Escribir por WhatsApp"),
                ],
            ),
            Field(
                "button_text",
                "Texto del botón",
                help="Opcional. Ej: Ver más, Escríbenos.",
                show_if={"button_action": ["page", "url", "whatsapp"]},
            ),
            Field(
                "button_page",
                "Página de destino",
                type="select",
                choices_source="pages",
                help="Página del sitio a la que llevará el botón.",
                show_if={"button_action": ["page"]},
            ),
            Field(
                "button_url",
                "Enlace externo",
                help="Ej: https://...",
                show_if={"button_action": ["url"]},
            ),
            Field(
                "button_message",
                "Mensaje de WhatsApp",
                type="textarea",
                rows=3,
                help="Opcional. Si se deja vacío se usa el contenido del modal.",
                show_if={"button_action": ["whatsapp"]},
            ),
            Field("delay", "Retardo (segundos)", type="number", help="Tiempo antes de mostrarse."),
            Field(
                "frequency",
                "Frecuencia",
                type="select",
                default="session",
                choices=[
                    ("session", "Una vez por sesión"),
                    ("always", "Siempre"),
                    ("once", "Una vez (recordar siempre)"),
                ],
            ),
            Field("order", "Orden", type="number"),
            Field("published", "Activo", type="bool"),
        ],
        columns=[
            {"name": "title", "label": "Titulo"},
            {
                "name": "button_action",
                "label": "Acción",
                "choices": [
                    ("none", "Sin botón"),
                    ("page", "Página del sitio"),
                    ("url", "Enlace externo"),
                    ("whatsapp", "WhatsApp"),
                ],
            },
            {"name": "frequency", "label": "Frecuencia"},
            {"name": "order", "label": "Orden", "type": "number"},
            {"name": "published", "label": "Activo", "type": "bool"},
        ],
        order_by="order",
        image_fields=["image"],
    ),
}


SUPERADMIN_AREAS = {"paginas"}


def require_superadmin():
    """Aborta con 403 si el usuario no es Super Admin."""
    if not current_user.is_superadmin:
        abort(403)


def get_entity(key):
    entity = ENTITIES.get(key)
    if entity is None:
        abort(404)
    if entity.key in SUPERADMIN_AREAS:
        require_superadmin()
    return entity


def _form_template(entity):
    if entity.key == "certificados":
        return "admin/certificate_form.html"
    return "admin/entity_form.html"


def _certificate_patrones_json():
    """JSON con los equipos ya certificados para autocompletar la tabla de patrones."""
    import json

    from app.cert_mech import patrones_source

    data = patrones_source(Certificate.query.all())
    return json.dumps(data, ensure_ascii=False)


def _select_signatures():
    """Firmas disponibles (publicadas primero) para el formulario del certificado."""
    return Signature.query.order_by(
        Signature.published.desc(), Signature.order, Signature.name
    ).all()


def apply_defaults(obj, entity):
    """Valores por defecto para los formularios de creacion."""
    for f in entity.fields:
        current = getattr(obj, f.name, None)
        if current is None:
            if f.type == "bool":
                setattr(obj, f.name, f.name == "published")
            elif f.type == "number":
                setattr(obj, f.name, 0)
            elif f.type == "select" and f.default:
                setattr(obj, f.name, f.default)


def resolve_choices(entity):
    """Resuelve las opciones dinamicas de los campos select."""
    for f in entity.fields:
        if f.choices_source == "categories" and not f.choices:
            f.choices = [
                (c.id, c.name)
                for c in Category.query.order_by(Category.order, Category.name).all()
            ]
        elif f.choices_source == "pages" and not f.choices:
            fixed = [
                ("/", "Inicio"),
                ("/nosotros", "Nosotros"),
                ("/servicios", "Servicios"),
                ("/ventas", "Ventas"),
                ("/alquiler", "Alquiler"),
                ("/capacitaciones", "Capacitaciones"),
                ("/soporte", "Soporte"),
                ("/certificados", "Certificados"),
                ("/contacto", "Contacto"),
            ]
            extra = [
                (f"/{p.slug}", p.title)
                for p in Page.query.filter_by(published=True).order_by(Page.order).all()
                if p.slug not in ("nosotros", "capacitaciones", "soporte")
            ]
            f.choices = fixed + extra
    return entity.fields


# --------------------------------------------------------------------------
# Escritura de campos desde el formulario
# --------------------------------------------------------------------------
def populate_object(obj, entity, form, files):
    has_slug = any(f.name == "slug" for f in entity.fields)
    for f in entity.fields:
        name = f.name
        if f.type == "bool":
            setattr(obj, name, form.get(name) in ("on", "1", "true", "yes"))
        elif f.type == "image":
            upload = files.get(name)
            if upload and getattr(upload, "filename", ""):
                path = save_upload(upload, subdir=entity.key)
                if path:
                    old = getattr(obj, name, "")
                    if old and old != path:
                        delete_upload(old)
                    setattr(obj, name, path)
        elif f.type == "number":
            raw = (form.get(name) or "").strip()
            setattr(obj, name, int(raw) if raw not in ("", None) else 0)
        elif f.type == "price":
            raw = (form.get(name) or "").strip().replace(".", "").replace(",", "")
            if raw:
                setattr(obj, name, float(raw))
            else:
                setattr(obj, name, None)
        elif f.type == "date":
            raw = (form.get(name) or "").strip()
            if raw:
                try:
                    setattr(obj, name, datetime.date.fromisoformat(raw))
                except ValueError:
                    setattr(obj, name, None)
            else:
                setattr(obj, name, None)
        elif f.type == "select":
            raw = form.get(name)
            if raw is None or raw == "":
                continue
            if name.endswith("_id"):
                setattr(obj, name, int(raw))
            else:
                setattr(obj, name, raw)
        else:
            setattr(obj, name, (form.get(name) or "").strip())

    # Slug: auto-generado si esta vacio
    if has_slug:
        raw_slug = (form.get("slug") or "").strip()
        if not raw_slug:
            base = form.get("name") or form.get("title") or form.get("serial") or "item"
            setattr(obj, "slug", unique_slug(entity.model, base, exclude_id=obj.id))
        else:
            setattr(obj, "slug", unique_slug(entity.model, raw_slug, exclude_id=obj.id))


# --------------------------------------------------------------------------
# Certificados (formulario personalizado con filas dinamicas)
# --------------------------------------------------------------------------
CERT_TEXT_FIELDS = [
    "serial", "client", "client_doc", "client_email", "client_address",
    "equipment", "equipment_brand", "equipment_model",
    "uncertainty", "std_wavelength",
    "test_equipment", "test_brand", "test_model", "test_serial", "test_notes",
    "certifier", "certifier_role", "notes",
]


def populate_certificate(obj, form, files):
    """Lee el formulario personalizado de certificados (incluye filas de pruebas)."""
    obj.cert_type = form.get("cert_type") or "calibracion"
    obj.device_type = form.get("device_type") or "opm"
    obj.doc_mode = form.get("doc_mode") or "generar"
    # El certificado mecanico se identifica por tipo de certificado y dispositivo.
    if "mecanica" in (obj.cert_type, obj.device_type):
        obj.cert_type = "mecanica"
        obj.device_type = "mecanica"
    # El titulo se deriva del tipo: no se pide al usuario.
    obj.title = Certificate.TYPES.get(obj.cert_type, "CERTIFICADO")

    for name in CERT_TEXT_FIELDS:
        if name in form:
            setattr(obj, name, (form.get(name) or "").strip())

    # Firma elegida de la lista (completa nombre, cargo e imagen).
    sig_raw = (form.get("signature_id") or "").strip()
    if sig_raw.isdigit():
        sig = db.session.get(Signature, int(sig_raw))
        if sig:
            obj.signature_id = sig.id
            if sig.name:
                obj.certifier = sig.name
            if sig.role:
                obj.certifier_role = sig.role
            if sig.image:
                obj.signature = sig.image
    else:
        obj.signature_id = None

    # Equipos de prueba (patron): lista JSON de texto libre.
    if "test_equipment_data" in form:
        import json

        raw_eq = (form.get("test_equipment_data") or "").strip()
        items = []
        if raw_eq:
            try:
                parsed = json.loads(raw_eq)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, list):
                items = [str(x).strip() for x in parsed if str(x).strip()]
        obj.test_equipment_data = json.dumps(items, ensure_ascii=False) if items else ""
        obj.test_equipment = items[0] if items else ""

    for name in ("issued_date", "next_date"):
        raw = (form.get(name) or "").strip()
        try:
            setattr(obj, name, datetime.date.fromisoformat(raw) if raw else None)
        except ValueError:
            setattr(obj, name, None)

    obj.published = form.get("published") in ("on", "1", "true", "yes")

    upload = files.get("file_url")
    if upload and getattr(upload, "filename", ""):
        path = save_upload(upload, subdir="certificados")
        if path:
            delete_upload(obj.file_url or "")
            obj.file_url = path

    signature = files.get("signature")
    if signature and getattr(signature, "filename", ""):
        path = save_upload(signature, subdir="certificados")
        if path:
            delete_upload(obj.signature or "")
            obj.signature = path

    if not obj.code:
        obj.code = new_cert_code()

    # Datos OTDR (JSON). Se normaliza para descartar valores vacios o invalidos.
    if "otdr_data" in form:
        from app.cert_otdr import parse_otdr, serialize_otdr

        raw_otdr = (form.get("otdr_data") or "").strip()
        obj.otdr_data = serialize_otdr(parse_otdr(raw_otdr)) if raw_otdr else ""

    # Datos del certificado de ajuste y calibracion mecanica (JSON).
    if "mech_data" in form:
        from app.cert_mech import serialize_mech

        raw_mech = (form.get("mech_data") or "").strip()
        obj.mech_data = serialize_mech(raw_mech) if raw_mech else ""
    if obj.device_type != "mecanica":
        obj.mech_data = None

    obj.tests.clear()
    indexes = set()
    for key in form.keys():
        match = re.match(r"tests-(\d+)-no$", key)
        if match:
            indexes.add(int(match.group(1)))
    for i in sorted(indexes):
        no = (form.get(f"tests-{i}-no") or "").strip()
        wavelength = (form.get(f"tests-{i}-wavelength") or "").strip()
        power = (form.get(f"tests-{i}-power") or "").strip()
        wavelength_value = (form.get(f"tests-{i}-wavelength_value") or "").strip()
        approved = form.get(f"tests-{i}-approved", "1") in ("1", "on", "true", "yes")
        if not any([no, wavelength, power, wavelength_value]):
            continue
        obj.tests.append(CertificateTest(
            test_no=no,
            wavelength=wavelength,
            power=power,
            wavelength_value=wavelength_value,
            approved=approved,
            order=i,
        ))


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
@admin_bp.before_request
@login_required
def guard():
    if not current_user.is_active:
        return redirect(url_for("auth.login"))
    return None


@admin_bp.route("/")
def dashboard():
    stats = {
        "paginas": Page.query.count(),
        "servicios": Service.query.count(),
        "productos": Product.query.count(),
        "marcas": Brand.query.count(),
        "certificados": Certificate.query.count(),
        "galeria": GalleryImage.query.count(),
        "modales": HomeModal.query.count(),
        "mensajes": ContactMessage.query.count(),
        "no_leidos": ContactMessage.query.filter_by(is_read=False).count(),
    }
    recent = (
        ContactMessage.query.order_by(ContactMessage.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent=recent,
        stats_no_leidos=stats["no_leidos"],
    )


@admin_bp.route("/<entity_key>")
def entity_list(entity_key):
    entity = get_entity(entity_key)
    page = request.args.get("page", 1, type=int)
    q = (request.args.get("q") or "").strip()

    query = entity.model.query
    if q:
        clauses = []
        for col in entity.model.__table__.columns:
            if col.type.__class__.__name__ in ("String", "Text"):
                clauses.append(col.like(f"%{q}%"))
        if clauses:
            query = query.filter(db.or_(*clauses))

    if entity.key == "certificados":
        orders = (entity.model.issued_date.desc(), entity.model.created_at.desc())
    else:
        orders = (_order_clause(entity.model, entity.order_by),)
    pagination = query.order_by(*orders).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "admin/entity_list.html",
        entity=entity,
        items=pagination.items,
        pagination=pagination,
        q=q,
        signatures=_select_signatures() if entity.key == "certificados" else [],
    )


@admin_bp.route("/<entity_key>/nuevo", methods=["GET", "POST"])
def entity_create(entity_key):
    entity = get_entity(entity_key)
    obj = entity.model()

    if request.method == "POST":
        if entity.key == "certificados":
            populate_certificate(obj, request.form, request.files)
        else:
            populate_object(obj, entity, request.form, request.files)
        try:
            db.session.add(obj)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo guardar el registro. Verifique los datos.", "error")
            return render_template(
                _form_template(entity),
                entity=entity,
                obj=obj,
                fields=resolve_choices(entity),
                creating=True,
                patrones_json=_certificate_patrones_json() if entity.key == "certificados" else "",
                signatures=_select_signatures() if entity.key == "certificados" else [],
            )
        flash(f"{entity.singular.capitalize()} guardado correctamente.", "success")
        return redirect(url_for("admin.entity_list", entity_key=entity.key))

    apply_defaults(obj, entity)
    return render_template(
        _form_template(entity),
        entity=entity,
        obj=obj,
        fields=resolve_choices(entity),
        creating=True,
        patrones_json=_certificate_patrones_json() if entity.key == "certificados" else "",
        signatures=_select_signatures() if entity.key == "certificados" else [],
    )


@admin_bp.route("/<entity_key>/<int:item_id>/editar", methods=["GET", "POST"])
def entity_edit(entity_key, item_id):
    entity = get_entity(entity_key)
    obj = db.session.get(entity.model, item_id) or abort(404)

    if request.method == "POST":
        if entity.key == "certificados":
            populate_certificate(obj, request.form, request.files)
        else:
            populate_object(obj, entity, request.form, request.files)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo actualizar el registro.", "error")
        else:
            flash(f"{entity.singular.capitalize()} actualizado correctamente.", "success")
        return redirect(url_for("admin.entity_list", entity_key=entity.key))

    return render_template(
        _form_template(entity),
        entity=entity,
        obj=obj,
        fields=resolve_choices(entity),
        creating=False,
        patrones_json=_certificate_patrones_json() if entity.key == "certificados" else "",
        signatures=_select_signatures() if entity.key == "certificados" else [],
    )


@admin_bp.route("/<entity_key>/<int:item_id>/eliminar", methods=["POST"])
def entity_delete(entity_key, item_id):
    entity = get_entity(entity_key)
    obj = db.session.get(entity.model, item_id)
    if obj:
        for f in entity.image_fields:
            delete_upload(getattr(obj, f, ""))
        db.session.delete(obj)
        db.session.commit()
        flash(f"{entity.singular.capitalize()} eliminado.", "success")
    return redirect(url_for("admin.entity_list", entity_key=entity.key))


def _order_clause(model, order_by):
    desc = order_by.startswith("-")
    col_name = order_by.lstrip("-")
    col = getattr(model, col_name, None) or model.id
    return col.desc() if desc else col.asc()


@admin_bp.route("/certificados/<int:item_id>/qr.png")
def certificate_qr(item_id):
    cert = db.session.get(Certificate, item_id) or abort(404)
    base = get_base_url({s.key: s.value for s in Setting.query.all()})
    verify_url = base + url_for("public.certificate_detail", code=cert.verify_code)
    png = qr_png(verify_url, logo_path=company_logo_path())
    if png is None:
        flash("La generacion de codigos QR no esta disponible.", "error")
        return redirect(url_for("admin.entity_list", entity_key="certificados"))
    filename = f"qr-{cert.serial or cert.id}.png".replace(" ", "_")
    response = Response(png, mimetype="image/png")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@admin_bp.route("/certificados/<int:item_id>/ticket.png")
def certificate_ticket(item_id):
    """Ticket del certificado como imagen (logo, datos y QR), listo para imprimir."""
    cert = db.session.get(Certificate, item_id) or abort(404)
    settings = {s.key: s.value for s in Setting.query.all()}
    base = get_base_url(settings)
    verify_url = base + url_for("public.certificate_detail", code=cert.verify_code)
    logo = company_logo_path()
    qr = qr_png(verify_url, logo_path=logo)

    from app.ticket import build_ticket_png

    png = build_ticket_png(cert, settings, qr_bytes=qr, logo_path=logo)
    if not png:
        flash("No se pudo generar el ticket.", "error")
        return redirect(url_for("admin.entity_list", entity_key="certificados"))
    response = Response(png, mimetype="image/png")
    response.headers["Content-Disposition"] = 'inline; filename="ticket.png"'
    return response


# --------------------------------------------------------------------------
# Firmas (se administran dentro de la vista de certificados)
# --------------------------------------------------------------------------
@admin_bp.route("/certificados/firmas/nueva", methods=["POST"])
def signature_create():
    name = (request.form.get("name") or "").strip()
    role = (request.form.get("role") or "").strip()
    if not name:
        flash("El nombre de la firma es obligatorio.", "error")
        return redirect(url_for("admin.entity_list", entity_key="certificados"))

    raw_order = (request.form.get("order") or "").strip()
    try:
        order = int(raw_order) if raw_order else 0
    except ValueError:
        order = 0

    image = ""
    upload = request.files.get("image")
    if upload and getattr(upload, "filename", ""):
        image = save_upload(upload, subdir="firmas") or ""

    db.session.add(
        Signature(
            name=name,
            role=role,
            image=image,
            order=order,
            published=request.form.get("published") in ("on", "1", "true", "yes"),
        )
    )
    db.session.commit()
    flash("Firma guardada correctamente.", "success")
    return redirect(url_for("admin.entity_list", entity_key="certificados"))


@admin_bp.route("/certificados/firmas/<int:item_id>/eliminar", methods=["POST"])
def signature_delete(item_id):
    sig = db.session.get(Signature, item_id)
    if sig:
        delete_upload(sig.image or "")
        db.session.delete(sig)
        db.session.commit()
        flash("Firma eliminada.", "success")
    return redirect(url_for("admin.entity_list", entity_key="certificados"))


# --------------------------------------------------------------------------
# Mensajes de contacto
# --------------------------------------------------------------------------
@admin_bp.route("/mensajes")
def messages():
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "admin/messages.html", items=pagination.items, pagination=pagination
    )


@admin_bp.route("/mensajes/<int:item_id>")
def message_detail(item_id):
    msg = db.session.get(ContactMessage, item_id) or abort(404)
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("admin/message_detail.html", msg=msg)


@admin_bp.route("/mensajes/<int:item_id>/eliminar", methods=["POST"])
def message_delete(item_id):
    msg = db.session.get(ContactMessage, item_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        flash("Mensaje eliminado.", "success")
    return redirect(url_for("admin.messages"))


@admin_bp.route("/mensajes/<int:item_id>/alternar", methods=["POST"])
def message_toggle(item_id):
    msg = db.session.get(ContactMessage, item_id)
    if msg:
        msg.is_read = not msg.is_read
        db.session.commit()
    return redirect(request.referrer or url_for("admin.messages"))


# --------------------------------------------------------------------------
# Ajustes del sitio
# --------------------------------------------------------------------------
@admin_bp.route("/ajustes", methods=["GET", "POST"])
def settings():
    require_superadmin()
    if request.method == "POST":
        for row in Setting.query.all():
            if row.field_type in ("image", "video"):
                upload = request.files.get(f"file_{row.key}")
                if upload and getattr(upload, "filename", ""):
                    path = save_upload(upload, subdir="settings")
                    if path:
                        delete_upload(row.value)
                        row.value = path
                else:
                    row.value = request.form.get(f"value_{row.key}", row.value)
            else:
                row.value = request.form.get(f"value_{row.key}", row.value)

        db.session.commit()
        flash("Ajustes guardados correctamente.", "success")
        return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html", sections=get_settings_by_section()
    )


# --------------------------------------------------------------------------
# Textos de la interfaz (etiquetas editables)
# --------------------------------------------------------------------------
@admin_bp.route("/textos", methods=["GET", "POST"])
def textos():
    require_superadmin()
    if request.method == "POST":
        for key, default in DEFAULT_LABELS.items():
            value = request.form.get(f"label_{key}")
            if value is None:
                continue
            row = Setting.query.filter_by(key=f"label_{key}").first()
            if row:
                row.value = value
            else:
                Setting.set(
                    f"label_{key}",
                    value,
                    label=default,
                    section="Textos de interfaz",
                    field_type="text",
                )
        db.session.commit()
        flash("Textos guardados correctamente.", "success")
        return redirect(url_for("admin.textos"))

    labels_overrides = {
        s.key[len("label_"):]: s.value
        for s in Setting.query.filter_by(section="Textos de interfaz").all()
        if s.key.startswith("label_")
    }
    return render_template(
        "admin/textos.html", labels=DEFAULT_LABELS, labels_overrides=labels_overrides
    )


# --------------------------------------------------------------------------
# Perfil del administrador
# --------------------------------------------------------------------------
@admin_bp.route("/perfil", methods=["GET", "POST"])
def profile():
    user = current_user
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        new_password = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        current_password = request.form.get("current_password") or ""

        if not user.check_password(current_password):
            flash("La contrasena actual es incorrecta.", "error")
        elif new_password and new_password != confirm:
            flash("La nueva contrasena y su confirmacion no coinciden.", "error")
        elif new_password and len(new_password) < 8:
            flash("La nueva contrasena debe tener al menos 8 caracteres.", "error")
        else:
            user.full_name = full_name
            user.email = email
            if new_password:
                user.set_password(new_password)
            db.session.commit()
            flash("Perfil actualizado correctamente.", "success")
            return redirect(url_for("admin.profile"))

    return render_template("admin/profile.html", user=user)


# --------------------------------------------------------------------------
# Usuarios (solo Super Admin; los Super Admin no se listan)
# --------------------------------------------------------------------------
@admin_bp.route("/usuarios")
def users():
    require_superadmin()
    items = (
        User.query.filter(User.role != "superadmin")
        .order_by(User.created_at.desc(), User.id.desc())
        .all()
    )
    total_superadmins = User.query.filter_by(role="superadmin").count()
    return render_template(
        "admin/users.html",
        items=items,
        roles=User.ROLES,
        total_superadmins=total_superadmins,
    )


@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
def user_create():
    require_superadmin()
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        full_name = (request.form.get("full_name") or "").strip()
        role = (request.form.get("role") or "admin").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        errors = []
        if role not in User.ROLES:
            role = "admin"
        if not username:
            errors.append("El nombre de usuario es obligatorio.")
        elif User.query.filter_by(username=username).first():
            errors.append("Ese nombre de usuario ya existe.")
        if email and User.query.filter_by(email=email).first():
            errors.append("Ese correo ya esta registrado.")
        if len(password) < 8:
            errors.append("La contrasena debe tener al menos 8 caracteres.")
        elif password != confirm:
            errors.append("La contrasena y su confirmacion no coinciden.")

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "admin/user_form.html", roles=User.ROLES, form=request.form, creating=True
            )

        user = User(
            username=username,
            email=email or None,
            full_name=full_name,
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html", roles=User.ROLES, form={}, creating=True
    )


@admin_bp.route("/usuarios/<int:item_id>/password", methods=["POST"])
def user_password(item_id):
    require_superadmin()
    user = db.session.get(User, item_id)
    if not user or user.role == "superadmin":
        abort(404)
    password = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""
    if len(password) < 8:
        flash("La contrasena debe tener al menos 8 caracteres.", "error")
    elif password != confirm:
        flash("La contrasena y su confirmacion no coinciden.", "error")
    else:
        user.set_password(password)
        db.session.commit()
        flash(f"Contrasena de {user.username} restablecida.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:item_id>/alternar", methods=["POST"])
def user_toggle(item_id):
    require_superadmin()
    user = db.session.get(User, item_id)
    if user and user.role != "superadmin":
        user.is_active_user = not user.is_active_user
        db.session.commit()
        estado = "activado" if user.is_active_user else "desactivado"
        flash(f"Usuario {user.username} {estado}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:item_id>/eliminar", methods=["POST"])
def user_delete(item_id):
    require_superadmin()
    user = db.session.get(User, item_id)
    if user and user.role != "superadmin" and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
        flash("Usuario eliminado.", "success")
    return redirect(url_for("admin.users"))
