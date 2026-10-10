import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(256), nullable=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(64), primary_key=True)
    label = db.Column(db.String(120), default="")
    section = db.Column(db.String(64), default="General")
    field_type = db.Column(db.String(20), default="text")  # text|textarea|image|url
    value = db.Column(db.Text, default="")

    @classmethod
    def get(cls, key, default=""):
        row = db.session.get(cls, key)
        return row.value if row and row.value is not None else default

    @classmethod
    def set(cls, key, value, **extra):
        row = db.session.get(cls, key)
        if row is None:
            row = Setting(key=key, **extra)
            db.session.add(row)
        row.value = value
        return row

    def as_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "section": self.section,
            "field_type": self.field_type,
            "value": self.value,
        }


class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    subtitle = db.Column(db.String(255), default="")
    body = db.Column(db.Text, default="")
    image = db.Column(db.String(255), default="")
    show_in_nav = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def by_slug(cls, slug):
        return db.session.scalar(
            db.select(cls).where(cls.slug == slug, cls.published.is_(True))
        )


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), default="")
    excerpt = db.Column(db.String(300), default="")
    body = db.Column(db.Text, default="")
    icon = db.Column(db.String(60), default="fiber")
    image = db.Column(db.String(255), default="")
    featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)

    products = db.relationship("Product", backref="category", lazy="dynamic")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(300), default="")
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(12, 2), nullable=True)  # None = consultar
    image = db.Column(db.String(255), default="")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    # venta | alquiler | ambos
    availability = db.Column(db.String(12), default="venta")
    featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def available_for(self, mode):
        return self.availability in (mode, "ambos")

    @property
    def price_display(self):
        if self.price is None:
            return "Consultar"
        return "${:,.0f}".format(float(self.price)).replace(",", ".")


class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    logo = db.Column(db.String(255), default="")
    url = db.Column(db.String(255), default="")
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(80), nullable=False, index=True)
    client = db.Column(db.String(160), default="")
    equipment = db.Column(db.String(160), default="")
    issued_date = db.Column(db.Date)
    file_url = db.Column(db.String(255), default="")
    notes = db.Column(db.String(255), default="")
    published = db.Column(db.Boolean, default=True)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), default="")
    phone = db.Column(db.String(40), default="")
    subject = db.Column(db.String(160), default="")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), default="")
    image = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(80), default="general")
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)


def unique_slug(model, base, exclude_id=None):
    """Genera un slug unico dentro del modelo indicado."""
    slugify = (
        base.strip()
        .lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("/", "-")
    )
    slug = slugify or "item"
    query = model.query.filter(model.slug == slug)
    if exclude_id:
        query = query.filter(model.id != exclude_id)
    counter = 1
    while query.first():
        counter += 1
        slug = f"{slugify}-{counter}"
        query = model.query.filter(model.slug == slug)
        if exclude_id:
            query = query.filter(model.id != exclude_id)
    return slug


def new_uuid_name(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"{uuid.uuid4().hex}.{ext}"
