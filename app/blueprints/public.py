import urllib.parse

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

from app.extensions import db
from app.models import (
    Certificate,
    ContactMessage,
    GalleryImage,
    HomeModal,
    Page,
    Product,
    Service,
)
from app.utils import base_context

public_bp = Blueprint("public", __name__)


def whatsapp_url(settings, text="Hola, me gustaria recibir mas informacion."):
    number = (settings.get("whatsapp") or "").replace("+", "").replace(" ", "")
    if not number:
        return settings.get("whatsapp_link", "#")
    return f"https://wa.me/{number}?text={urllib.parse.quote(text)}"


@public_bp.app_context_processor
def inject_whatsapp():
    settings = base_context()["settings"]
    return {
        "whatsapp_url": whatsapp_url(settings),
        "wa": lambda text: whatsapp_url(settings, text),
    }


@public_bp.route("/")
def index():
    settings = base_context()["settings"]
    services = Service.query.filter_by(published=True).order_by(Service.order).all()
    featured_services = [s for s in services if s.featured] or services[:3]
    gallery = (
        GalleryImage.query.filter_by(published=True)
        .order_by(GalleryImage.order)
        .limit(6)
        .all()
    )
    home_modals = (
        HomeModal.query.filter_by(published=True).order_by(HomeModal.order).all()
    )
    return render_template(
        "index.html",
        settings=settings,
        services=featured_services,
        gallery=gallery,
        home_modals=home_modals,
    )


@public_bp.route("/servicios")
def services():
    services = Service.query.filter_by(published=True).order_by(Service.order).all()
    return render_template("services.html", services=services)


def render_page(slug):
    page = Page.by_slug(slug)
    if page is None:
        abort(404)
    return render_template("page.html", page=page)


@public_bp.route("/nosotros")
def nosotros():
    return render_page("nosotros")


@public_bp.route("/capacitaciones")
def capacitaciones():
    return render_page("capacitaciones")


@public_bp.route("/soporte")
def soporte():
    return render_page("soporte")


def catalog(mode):
    page = request.args.get("page", 1, type=int)
    q = (request.args.get("q") or "").strip()
    cat = (request.args.get("cat") or "").strip()

    query = Product.query.filter_by(published=True)
    query = query.filter(
        db.or_(Product.availability == mode, Product.availability == "ambos")
    )
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.name.like(like), Product.summary.like(like)))
    if cat:
        query = query.join(Product.category).filter_by(slug=cat)

    pagination = query.order_by(Product.order, Product.id.desc()).paginate(
        page=page, per_page=app_products_per_page(), error_out=False
    )
    return render_template(
        "products.html",
        mode=mode,
        products=pagination.items,
        pagination=pagination,
        q=q,
        cat=cat,
    )


def app_products_per_page():
    from flask import current_app

    return current_app.config["PRODUCTS_PER_PAGE"]


@public_bp.route("/ventas")
def ventas():
    return catalog("venta")


@public_bp.route("/alquiler")
def alquiler():
    return catalog("alquiler")


@public_bp.route("/producto/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, published=True).first_or_404()
    settings = base_context()["settings"]
    message = f"Hola, estoy interesado en: {product.name}"
    if product.price is not None:
        message += f" - Precio: {product.price_display}"
    return render_template(
        "product_detail.html",
        product=product,
        wa=whatsapp_url(settings, message),
    )


@public_bp.route("/contacto", methods=["GET", "POST"])
def contacto():
    settings = base_context()["settings"]
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        errors = []
        if not name:
            errors.append("El nombre es obligatorio.")
        if not message:
            errors.append("El mensaje es obligatorio.")
        if email and "@" not in email:
            errors.append("El correo electronico no es valido.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "contact.html",
                form=request.form,
                error=True,
            )

        db.session.add(
            ContactMessage(
                name=name, email=email, phone=phone, subject=subject, message=message
            )
        )
        db.session.commit()
        flash("Mensaje enviado correctamente. Le responderemos pronto.", "success")
        return redirect(url_for("public.contacto"))

    return render_template("contact.html", form={})


@public_bp.route("/certificados")
def certificados():
    q = (request.args.get("q") or "").strip()
    results = None
    if q:
        like = f"%{q}%"
        results = (
            Certificate.query.filter(
                Certificate.published.is_(True),
                db.or_(
                    Certificate.serial.like(like),
                    Certificate.client.like(like),
                    Certificate.equipment.like(like),
                ),
            )
            .order_by(Certificate.issued_date.desc())
            .all()
        )
    return render_template("certificates.html", q=q, results=results)


@public_bp.route("/<slug>")
def page_fallback(slug):
    """Permite crear nuevas paginas desde el panel de administracion."""
    page = Page.by_slug(slug)
    if page is None:
        abort(404)
    return render_template("page.html", page=page)


@public_bp.route("/robots.txt")
def robots():
    base = base_context()["base_url"]
    txt = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return Response(txt, mimetype="text/plain; charset=utf-8")


@public_bp.route("/sitemap.xml")
def sitemap():
    base = base_context()["base_url"]
    locs = {f"{base}{p}" for p in [
        "/",
        "/nosotros",
        "/servicios",
        "/ventas",
        "/alquiler",
        "/capacitaciones",
        "/soporte",
        "/certificados",
        "/contacto",
    ]}
    for page in Page.query.filter_by(published=True).all():
        locs.add(f"{base}/{page.slug}")
    for product in Product.query.filter_by(published=True).all():
        locs.add(f"{base}/producto/{product.slug}")
    entries = "\n".join(f"  <url><loc>{loc}</loc></url>" for loc in sorted(locs))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    return Response(xml, mimetype="application/xml; charset=utf-8")
