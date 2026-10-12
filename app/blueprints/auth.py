import time
from threading import Lock

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

auth_bp = Blueprint("auth", __name__)

# --- Proteccion anti fuerza bruta (en memoria, por IP) ---
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300
_attempts = {}
_attempts_lock = Lock()


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "desconocido"


def _is_blocked(ip):
    now = time.time()
    with _attempts_lock:
        times = [t for t in _attempts.get(ip, []) if now - t < _WINDOW_SECONDS]
        if times:
            _attempts[ip] = times
        else:
            _attempts.pop(ip, None)
        return len(times) >= _MAX_ATTEMPTS


def _register_failure(ip):
    with _attempts_lock:
        _attempts.setdefault(ip, []).append(time.time())
        if len(_attempts) > 5000:
            _prune_locked()


def _clear_failures(ip):
    with _attempts_lock:
        _attempts.pop(ip, None)


def _prune_locked():
    now = time.time()
    for key in list(_attempts.keys()):
        times = [t for t in _attempts[key] if now - t < _WINDOW_SECONDS]
        if times:
            _attempts[key] = times
        else:
            _attempts.pop(key, None)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        ip = _client_ip()
        if _is_blocked(ip):
            flash(
                "Demasiados intentos fallidos. Espere unos minutos antes de volver a intentar.",
                "error",
            )
            return render_template("admin/login.html"), 429

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(username=username).first()
        if user and user.is_active and user.check_password(password):
            _clear_failures(ip)
            login_user(user, remember=remember)
            flash(f"Bienvenido(a), {user.full_name or user.username}.", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))
        _register_failure(ip)
        flash("Usuario o contrasena incorrectos.", "error")

    return render_template("admin/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada correctamente.", "success")
    return redirect(url_for("auth.login"))
