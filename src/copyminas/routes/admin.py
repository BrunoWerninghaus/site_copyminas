import hmac
import secrets
import time
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.copyminas.catalog import get_public_categories, get_public_products
from src.copyminas.db import DatabaseUnavailable


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

_ADMIN_SESSION_KEY = "copyminas_admin_authenticated"
_ADMIN_CSRF_KEY = "copyminas_admin_csrf"
_ADMIN_FAILURES_KEY = "copyminas_admin_failures"
_ADMIN_LOCKED_UNTIL_KEY = "copyminas_admin_locked_until"

_MAX_ATTEMPTS = 5
_LOCK_SECONDS = 60


def _configured():
    return bool(
        current_app.config.get("ADMIN_USERNAME", "").strip()
        and current_app.config.get("ADMIN_PASSWORD", "")
    )


def _csrf_token():
    token = session.get(_ADMIN_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_ADMIN_CSRF_KEY] = token
    return token


def _csrf_valid(token):
    expected = session.get(_ADMIN_CSRF_KEY, "")
    return bool(
        token
        and expected
        and hmac.compare_digest(str(token), str(expected))
    )


def _locked_seconds():
    locked_until = float(session.get(_ADMIN_LOCKED_UNTIL_KEY, 0) or 0)
    remaining = int(locked_until - time.time())
    if remaining <= 0:
        session.pop(_ADMIN_LOCKED_UNTIL_KEY, None)
        session.pop(_ADMIN_FAILURES_KEY, None)
        return 0
    return remaining


def _register_failure():
    failures = int(session.get(_ADMIN_FAILURES_KEY, 0) or 0) + 1
    session[_ADMIN_FAILURES_KEY] = failures

    if failures >= _MAX_ATTEMPTS:
        session[_ADMIN_LOCKED_UNTIL_KEY] = time.time() + _LOCK_SECONDS


def _clear_failures():
    session.pop(_ADMIN_FAILURES_KEY, None)
    session.pop(_ADMIN_LOCKED_UNTIL_KEY, None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get(_ADMIN_SESSION_KEY):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get(_ADMIN_SESSION_KEY):
        return redirect(url_for("admin.dashboard"))

    if not _configured():
        return (
            render_template(
                "admin/login.html",
                admin_unconfigured=True,
                login_error=None,
                locked_seconds=0,
                csrf_token=_csrf_token(),
            ),
            503,
        )

    locked_seconds = _locked_seconds()
    login_error = None
    status = 200

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            login_error = "Sessão de login expirada. Recarregue a página e tente novamente."
            status = 400
        elif locked_seconds:
            login_error = (
                "Muitas tentativas inválidas. "
                f"Tente novamente em aproximadamente {locked_seconds} segundos."
            )
            status = 429
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            valid_username = hmac.compare_digest(
                username,
                current_app.config["ADMIN_USERNAME"],
            )
            valid_password = hmac.compare_digest(
                password,
                current_app.config["ADMIN_PASSWORD"],
            )

            if valid_username and valid_password:
                session.clear()
                session[_ADMIN_SESSION_KEY] = True
                session[_ADMIN_CSRF_KEY] = secrets.token_urlsafe(32)
                return redirect(url_for("admin.dashboard"))

            _register_failure()
            login_error = "Credenciais inválidas."
            status = 401
            locked_seconds = _locked_seconds()

    return (
        render_template(
            "admin/login.html",
            admin_unconfigured=False,
            login_error=login_error,
            locked_seconds=locked_seconds,
            csrf_token=_csrf_token(),
        ),
        status,
    )


@admin_bp.get("")
@login_required
def dashboard():
    catalog_available = True
    products = []
    categories = []

    try:
        products = get_public_products()
        categories = get_public_categories(products)
    except DatabaseUnavailable as exc:
        catalog_available = False
        current_app.logger.error("Admin catalog summary unavailable: %s", exc)

    return render_template(
        "admin/dashboard.html",
        catalog_available=catalog_available,
        product_count=len(products),
        category_count=len(categories),
        csrf_token=_csrf_token(),
    )


@admin_bp.post("/logout")
@login_required
def logout():
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return (
            render_template(
                "admin/error.html",
                title="Sessão inválida",
                message="Não foi possível encerrar a sessão com este formulário.",
            ),
            400,
        )

    session.clear()
    return redirect(url_for("admin.login"))
