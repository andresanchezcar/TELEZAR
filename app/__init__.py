import os

from flask import Flask, render_template

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    register_error_handlers(app)
    register_template_helpers(app)

    return app


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
