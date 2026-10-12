import os

from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-secreta-por-defecto-cambiar")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASEDIR, "instance", "telezarcomunicaciones.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    UPLOAD_FOLDER = os.path.join(BASEDIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB por archivo
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "pdf"}

    # Dominio publico (canonical, sitemap, Open Graph). Si no se define, usa telezarcomunicaciones.com
    SITE_URL = os.environ.get("SITE_URL", "https://telezarcomunicaciones.com/").rstrip("/")

    # Paginacion
    PRODUCTS_PER_PAGE = 12
