import os

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "copyminas-dev-only-change-me",
    )

    from .routes.public import public_bp

    app.register_blueprint(public_bp)

    return app
