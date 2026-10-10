import os

from flask import current_app, flash, redirect, url_for
from werkzeug.utils import secure_filename

from app.models import Brand, Category, Page, Service, Setting
from app.extensions import db


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


def get_settings():
    return {s.key: s.value for s in Setting.query.all()}


def get_settings_by_section():
    sections = {}
    for s in Setting.query.order_by(Setting.section, Setting.key).all():
        sections.setdefault(s.section, []).append(s)
    return sections


def base_context():
    """Contexto comun a todas las plantillas publicas."""
    settings = get_settings()
    pages = Page.query.filter_by(published=True).order_by(Page.order).all()
    return {
        "settings": settings,
        "nav_pages": pages,
        "nav_services": Service.query.filter_by(published=True)
        .order_by(Service.order)
        .all(),
        "categories": Category.query.filter_by(published=True)
        .order_by(Category.order)
        .all(),
        "brands": Brand.query.filter_by(published=True).order_by(Brand.order).all(),
    }
