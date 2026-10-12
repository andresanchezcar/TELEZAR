import os
import secrets

from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))


def _load_secret_key():
    """Clave secreta: usa SECRET_KEY del entorno; si no existe, genera una
    aleatoria y la guarda en instance/.secret_key para que las sesiones sean
    estables entre reinicios."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_path = os.path.join(BASEDIR, "instance", ".secret_key")
    try:
        if os.path.isfile(key_path):
            with open(key_path, "r", encoding="utf-8") as fh:
                stored = fh.read().strip()
            if stored:
                return stored
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        generated = secrets.token_hex(32)
        with open(key_path, "w", encoding="utf-8") as fh:
            fh.write(generated)
        return generated
    except OSError:
        return secrets.token_hex(32)


class Config:
    SECRET_KEY = _load_secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASEDIR, "instance", "telezarcomunicaciones.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    UPLOAD_FOLDER = os.path.join(BASEDIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB por archivo
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

    # Cookies de sesion
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # se activa automaticamente sobre HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Dominio publico (canonical, sitemap, Open Graph). Si no se define, usa telezarcomunicaciones.com
    SITE_URL = os.environ.get("SITE_URL", "https://telezarcomunicaciones.com/").rstrip("/")

    # Paginacion
    PRODUCTS_PER_PAGE = 12
