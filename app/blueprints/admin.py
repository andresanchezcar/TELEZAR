import datetime
from dataclasses import dataclass, field as dc_field
from typing import List, Optional

from flask import (
    Blueprint,
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
    ContactMessage,
    GalleryImage,
    Page,
    Product,
    Service,
    Setting,
    User,
    unique_slug,
)
from app.utils import delete_upload, get_settings_by_section, save_upload

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
            {"name": "client", "label": "Cliente"},
            {"name": "equipment", "label": "Equipo"},
            {"name": "issued_date", "label": "Emitido", "type": "date"},
            {"name": "published", "label": "Publicado", "type": "bool"},
        ],
        order_by="-issued_date",
        image_fields=["file_url"],
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
}


def get_entity(key):
    entity = ENTITIES.get(key)
    if entity is None:
        abort(404)
    return entity


def apply_defaults(obj, entity):
    """Valores por defecto para los formularios de creacion."""
    for f in entity.fields:
        current = getattr(obj, f.name, None)
        if current is None:
            if f.type == "bool":
                setattr(obj, f.name, f.name == "published")
            elif f.type == "number":
                setattr(obj, f.name, 0)


def resolve_choices(entity):
    """Resuelve las opciones dinamicas de los campos select."""
    for f in entity.fields:
        if f.choices_source == "categories" and not f.choices:
            f.choices = [
                (c.id, c.name)
                for c in Category.query.order_by(Category.order, Category.name).all()
            ]
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

    order = _order_clause(entity.model, entity.order_by)
    pagination = query.order_by(order).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "admin/entity_list.html",
        entity=entity,
        items=pagination.items,
        pagination=pagination,
        q=q,
    )


@admin_bp.route("/<entity_key>/nuevo", methods=["GET", "POST"])
def entity_create(entity_key):
    entity = get_entity(entity_key)
    obj = entity.model()

    if request.method == "POST":
        populate_object(obj, entity, request.form, request.files)
        try:
            db.session.add(obj)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo guardar el registro. Verifique los datos.", "error")
            return render_template(
                "admin/entity_form.html",
                entity=entity,
                obj=obj,
                fields=resolve_choices(entity),
                creating=True,
            )
        flash(f"{entity.singular.capitalize()} guardado correctamente.", "success")
        return redirect(url_for("admin.entity_list", entity_key=entity.key))

    apply_defaults(obj, entity)
    return render_template(
        "admin/entity_form.html",
        entity=entity,
        obj=obj,
        fields=resolve_choices(entity),
        creating=True,
    )


@admin_bp.route("/<entity_key>/<int:item_id>/editar", methods=["GET", "POST"])
def entity_edit(entity_key, item_id):
    entity = get_entity(entity_key)
    obj = db.session.get(entity.model, item_id) or abort(404)

    if request.method == "POST":
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
        "admin/entity_form.html",
        entity=entity,
        obj=obj,
        fields=resolve_choices(entity),
        creating=False,
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
    if request.method == "POST":
        for row in Setting.query.all():
            if row.field_type == "image":
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

        # Alta rapida de un ajuste nuevo
        new_key = (request.form.get("new_key") or "").strip()
        if new_key:
            Setting.set(
                new_key,
                request.form.get("new_value", ""),
                label=request.form.get("new_label", new_key),
                section=request.form.get("new_section", "General"),
                field_type=request.form.get("new_type", "text"),
            )
        db.session.commit()
        flash("Ajustes guardados correctamente.", "success")
        return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html", sections=get_settings_by_section()
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
