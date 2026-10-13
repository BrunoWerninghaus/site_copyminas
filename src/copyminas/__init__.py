import os
from secrets import token_urlsafe

from dotenv import load_dotenv
from flask import Flask, render_template

from .contact_abuse import install_contact_abuse
from .security import install_security_headers


def _env(primary, legacy, default=""):
    value = os.getenv(primary)
    if value is not None:
        return value

    legacy_value = os.getenv(legacy)
    if legacy_value is not None:
        return legacy_value

    return default


def create_app() -> Flask:
    # Site 2 already used a local .env for main_bd. Keep that contract
    # compatible while allowing the shorter DB_* names in Site 3.
    load_dotenv(".env")

    app = Flask(__name__)

    environment = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).strip().lower()
    if environment not in {"development", "test", "testing", "production", "prod"}:
        raise RuntimeError("APP_ENV must be development, testing, or production.")
    production = environment in {"production", "prod"}
    configured_secret = os.getenv("SECRET_KEY", "").strip()
    smtp_security = os.getenv("SMTP_SECURITY", "starttls").strip().lower()

    if smtp_security not in {"none", "starttls", "ssl"}:
        raise RuntimeError("SMTP_SECURITY must be none, starttls, or ssl.")

    if production:
        if len(configured_secret) < 32 or configured_secret.startswith(
            ("change-me", "copyminas-dev-only")
        ):
            raise RuntimeError(
                "Production requires a strong, unique SECRET_KEY (at least 32 characters)."
            )
        if smtp_security == "none":
            raise RuntimeError(
                "Production SMTP must use STARTTLS or SSL; plaintext is forbidden."
            )
        if os.getenv("FLASK_DEBUG", "0").strip() == "1":
            raise RuntimeError("FLASK_DEBUG must be disabled in production.")

    # The development fallback is random per process, never a published signing key.
    app.config["SECRET_KEY"] = configured_secret or token_urlsafe(48)

    app.config.update(
        DB_HOST=_env("DB_HOST", "DATABASE_HOST", "127.0.0.1"),
        DB_PORT=int(_env("DB_PORT", "DATABASE_PORT", "3306")),
        DB_NAME=_env("DB_NAME", "DATABASE_NAME", "main_bd"),
        DB_USER=_env("DB_USER", "DATABASE_USER", "root"),
        DB_PASSWORD=_env("DB_PASSWORD", "DATABASE_PASSWORD", ""),
        SMTP_HOST=os.getenv("SMTP_HOST", "smtp.copyminas.com.br"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_SECURITY=smtp_security,
        IS_PRODUCTION=production,
        SESSION_COOKIE_SECURE=production,
        SMTP_USER=os.getenv("SMTP_USER", "ti.processos@copyminas.com.br"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        CONTACT_NOTIFICATION_FROM=os.getenv(
            "CONTACT_NOTIFICATION_FROM",
            "ti.processos@copyminas.com.br",
        ),
        CONTACT_NOTIFICATION_TO=os.getenv(
            "CONTACT_NOTIFICATION_TO",
            "ti.processos@copyminas.com.br",
        ),
        CATALOG_SOURCE=os.getenv("CATALOG_SOURCE", "database").lower(),
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", ""),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", ""),
        MAX_CONTENT_LENGTH=int(os.getenv("ADMIN_UPLOAD_MAX_MB", "25")) * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    from .routes.admin import admin_bp
    from .routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    install_security_headers(app)
    install_contact_abuse(app)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("public/not_found.html"), 404

    return app
