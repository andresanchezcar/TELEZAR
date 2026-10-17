import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLES = {
        "admin": "Administrador",
        "superadmin": "Super Admin",
    }

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="admin", nullable=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user

    @property
    def is_superadmin(self):
        return self.role == "superadmin"

    @property
    def role_label(self):
        return self.ROLES.get(self.role, self.role or "Administrador")


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


class Signature(db.Model):
    __tablename__ = "signatures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    role = db.Column(db.String(120), default="")
    image = db.Column(db.String(255), default="")
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certificate(db.Model):
    __tablename__ = "certificates"

    # tipos soportados: calibracion (los demas se agregan a futuro)
    TYPES = {
        "calibracion": "CERTIFICADO DE CALIBRACIÓN",
        "mecanica": "CERTIFICADO DE AJUSTE Y CALIBRACIÓN MECÁNICA",
    }
    # dispositivos que se calibran
    DEVICE_TYPES = {
        "opm": "OPM (Medidor de potencia óptica)",
        "otdr": "OTDR (Reflectómetro óptico)",
        "mecanica": "Máquina de empalme por fusión (Ajuste y calibración mecánica)",
    }
    # forma de emision del documento
    MODES = {
        "generar": "Generar en sistema",
        "anexar": "Anexar documento",
    }

    id = db.Column(db.Integer, primary_key=True)
    cert_type = db.Column(db.String(30), default="calibracion")
    device_type = db.Column(db.String(20), default="opm")
    doc_mode = db.Column(db.String(20), default="generar")
    code = db.Column(db.String(24), unique=True, index=True)
    title = db.Column(db.String(160), default="CERTIFICADO DE CALIBRACIÓN")
    serial = db.Column(db.String(80), nullable=False, index=True)

    # datos del cliente
    client = db.Column(db.String(160), default="")           # razon social
    client_doc = db.Column(db.String(60), default="")        # documento / NIT
    client_email = db.Column(db.String(120), default="")
    client_address = db.Column(db.String(200), default="")   # direccion

    # datos del equipo a certificar
    equipment = db.Column(db.String(160), default="")
    equipment_brand = db.Column(db.String(120), default="")
    equipment_model = db.Column(db.String(120), default="")
    uncertainty = db.Column(db.String(30), default="")       # incertidumbre (%)
    std_wavelength = db.Column(db.String(60), default="")    # longitud de onda estandar
    issued_date = db.Column(db.Date)                         # fecha de calibracion
    next_date = db.Column(db.Date)                           # proxima calibracion

    # datos del equipo de prueba (patron utilizado)
    test_equipment = db.Column(db.String(160), default="")
    test_brand = db.Column(db.String(120), default="")
    test_model = db.Column(db.String(120), default="")
    test_serial = db.Column(db.String(80), default="")
    test_notes = db.Column(db.String(255), default="")
    test_equipment_data = db.Column(db.Text)  # JSON: lista de equipos de prueba (patron)

    # datos de quien certifica
    certifier = db.Column(db.String(160), default="")
    certifier_role = db.Column(db.String(120), default="")
    signature = db.Column(db.String(255), default="")  # imagen de la firma
    signature_id = db.Column(db.Integer, db.ForeignKey("signatures.id"))  # firma elegida

    file_url = db.Column(db.String(255), default="")
    notes = db.Column(db.String(255), default="")
    otdr_data = db.Column(db.Text)  # JSON con los datos del certificado OTDR
    mech_data = db.Column(db.Text)  # JSON con los datos del certificado de ajuste mecanico
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tests = db.relationship(
        "CertificateTest",
        backref="certificate",
        cascade="all, delete-orphan",
        order_by="CertificateTest.order",
        lazy="select",
    )

    @property
    def type_label(self):
        return self.TYPES.get(self.cert_type, "Certificado")

    @property
    def device_label(self):
        return self.DEVICE_TYPES.get(self.device_type, self.device_type or "")

    @property
    def mode_label(self):
        return self.MODES.get(self.doc_mode, self.doc_mode or "")

    @property
    def is_attachment_mode(self):
        return self.doc_mode == "anexar"

    @property
    def otdr(self):
        from app.cert_otdr import build_otdr_view

        return build_otdr_view(self.otdr_data)

    @property
    def mech(self):
        from app.cert_mech import build_mech_view

        return build_mech_view(self.mech_data)

    @property
    def test_equipments(self):
        """Lista de equipos de prueba (patron), con respaldo en el campo simple."""
        import json

        raw = (self.test_equipment_data or "").strip()
        if raw:
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                data = None
            if isinstance(data, list):
                items = [str(x).strip() for x in data if str(x).strip()]
                if items:
                    return items
        single = (self.test_equipment or "").strip()
        return [single] if single else []

    @property
    def verify_code(self):
        return self.code or str(self.id)

    @property
    def is_current(self):
        if not self.published:
            return False
        if self.next_date and self.next_date < datetime.utcnow().date():
            return False
        return True


class CertificateTest(db.Model):
    __tablename__ = "certificate_tests"

    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(
        db.Integer, db.ForeignKey("certificates.id"), nullable=False, index=True
    )
    order = db.Column(db.Integer, default=0)
    test_no = db.Column(db.String(20), default="")
    wavelength = db.Column(db.String(30), default="")        # longitud de onda (nm)
    power = db.Column(db.String(30), default="")             # potencia (dBm)
    wavelength_value = db.Column(db.String(30), default="")  # valor ±0.020nm
    approved = db.Column(db.Boolean, default=True)


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


class HomeModal(db.Model):
    __tablename__ = "home_modals"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, default="")
    image = db.Column(db.String(255), default="")
    button_text = db.Column(db.String(80), default="")
    button_action = db.Column(db.String(20), default="none")  # none|page|url|whatsapp
    button_page = db.Column(db.String(255), default="")
    button_url = db.Column(db.String(255), default="")
    button_message = db.Column(db.Text, default="")
    delay = db.Column(db.Integer, default=0)
    frequency = db.Column(db.String(20), default="session")
    order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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


def new_cert_code():
    """Codigo publico unico para verificacion de un certificado."""
    return uuid.uuid4().hex[:12].upper()
