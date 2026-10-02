import pymysql
from flask import current_app
from pymysql.cursors import DictCursor


class DatabaseUnavailable(RuntimeError):
    pass


def open_database():
    try:
        return pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config.get("DB_PASSWORD", ""),
            database=current_app.config.get("DB_NAME", "main_bd"),
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:
        code = exc.args[0] if exc.args else "unknown"
        detail = exc.args[1] if len(exc.args) > 1 else str(exc)
        raise DatabaseUnavailable(
            f"MySQL main_bd connection failed [{code}]: {detail}"
        ) from exc
