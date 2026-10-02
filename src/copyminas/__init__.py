import os

from dotenv import load_dotenv
from flask import Flask, render_template


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

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "copyminas-dev-only-change-me",
    )

    app.config.update(
        DB_HOST=_env("DB_HOST", "DATABASE_HOST", "127.0.0.1"),
        DB_PORT=int(_env("DB_PORT", "DATABASE_PORT", "3306")),
        DB_NAME=_env("DB_NAME", "DATABASE_NAME", "main_bd"),
        DB_USER=_env("DB_USER", "DATABASE_USER", "root"),
        DB_PASSWORD=_env("DB_PASSWORD", "DATABASE_PASSWORD", ""),
        SMTP_HOST=os.getenv("SMTP_HOST", "smtp.copyminas.com.br"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_SECURITY=os.getenv("SMTP_SECURITY", "none").lower(),
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
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    from .routes.admin import admin_bp
    from .routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("public/not_found.html"), 404

    return app
