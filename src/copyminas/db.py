import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class DatabaseUnavailable(RuntimeError):
    pass


def open_database():
    user = current_app.config.get("DB_USER", "")
    if not user:
        raise DatabaseUnavailable(
            "DB_USER is not configured for the main_bd connection."
        )

    try:
        return pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=user,
            password=current_app.config.get("DB_PASSWORD", ""),
            database=current_app.config.get("DB_NAME", "main_bd"),
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:
        raise DatabaseUnavailable("Could not connect to main_bd.") from exc
