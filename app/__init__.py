import os

from flask import Flask, render_template, request

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite:///"):
        db_dir = os.path.dirname(uri[len("sqlite:///"):])
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    register_error_handlers(app)
    register_template_helpers(app)
    register_security(app)

    return app


def register_security(app):
    """Cookies seguras y cabeceras de seguridad (sin romper el sitio)."""
    forced_secure = os.environ.get("SESSION_COOKIE_SECURE")

    @app.before_request
    def _secure_cookies():
        if forced_secure is not None:
            app.config["SESSION_COOKIE_SECURE"] = forced_secure == "1"
        else:
            proto = request.headers.get("X-Forwarded-Proto") or request.environ.get(
                "wsgi.url_scheme", ""
            )
            app.config["SESSION_COOKIE_SECURE"] = proto == "https"

    @app.after_request
    def _security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        if request.is_secure or request.headers.get("X-Forwarded-Proto") == "https":
            resp.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return resp


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("500.html"), 500


def register_template_helpers(app):
    from datetime import datetime

    from app.utils import base_context

    @app.context_processor
    def inject_globals():
        ctx = base_context()
        ctx["current_year"] = datetime.utcnow().year
        return ctx

    @app.template_filter("money")
    def money(value):
        if value is None:
            return "Consultar"
        return "${:,.0f}".format(float(value)).replace(",", ".")

    @app.template_filter("date_es")
    def date_es(value):
        if not value:
            return ""
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        try:
            return f"{value.day} de {meses[value.month - 1]} de {value.year}"
        except (AttributeError, ValueError, IndexError):
            return str(value)
