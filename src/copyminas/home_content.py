import json

import pymysql

from src.copyminas.db import DatabaseUnavailable, open_database


class HomeContentError(RuntimeError):
    pass


class HomeContentNotInitialized(HomeContentError):
    pass


def _missing_table(exc):
    return isinstance(exc, pymysql.MySQLError) and bool(exc.args) and exc.args[0] == 1146


def _database_error(exc, action):
    if isinstance(exc, DatabaseUnavailable):
        return exc
    if _missing_table(exc):
        return HomeContentNotInitialized("O módulo Home ainda não foi inicializado.")
    if isinstance(exc, pymysql.MySQLError):
        code = exc.args[0] if exc.args else "unknown"
        detail = exc.args[1] if len(exc.args) > 1 else str(exc)
        return DatabaseUnavailable(
            f"MySQL main_bd home {action} failed [{code}]: {detail}"
        )
    return HomeContentError(f"Home content {action} failed: {exc}")


def _decode_featured_ids(raw):
    if isinstance(raw, (list, tuple)):
        values = raw
    else:
        try:
            values = json.loads(raw or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            values = []

    result = []
    for value in values:
        try:
            product_id = int(value)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and product_id not in result:
            result.append(product_id)
    return result[:6]


def _hydrate_config(row):
    if row is None:
        return None
    item = dict(row)
    item["featured_product_ids"] = _decode_featured_ids(
        item.get("featured_product_ids")
    )
    for key in (
        "announcement_active",
        "show_solutions",
        "show_company",
        "show_location",
    ):
        item[key] = bool(item.get(key))
    return item


def home_schema_ready():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'site_home_config'")
            config_exists = cursor.fetchone() is not None
            cursor.execute("SHOW TABLES LIKE 'site_home_news'")
            news_exists = cursor.fetchone() is not None
            return config_exists and news_exists
    except Exception as exc:
        raise _database_error(exc, "schema check") from exc
    finally:
        connection.close()


def initialize_home_schema(default_config, featured_product_ids=None):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS site_home_config (
                    id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
                    announcement_active TINYINT(1) NOT NULL DEFAULT 0,
                    announcement_label VARCHAR(80) NOT NULL DEFAULT 'AVISO',
                    announcement_text VARCHAR(255) NOT NULL DEFAULT '',
                    announcement_link_label VARCHAR(80) NOT NULL DEFAULT '',
                    announcement_link_url VARCHAR(255) NOT NULL DEFAULT '',
                    hero_kicker VARCHAR(180) NOT NULL,
                    hero_title VARCHAR(255) NOT NULL,
                    hero_summary TEXT NOT NULL,
                    primary_cta_label VARCHAR(80) NOT NULL,
                    primary_cta_url VARCHAR(255) NOT NULL,
                    secondary_cta_label VARCHAR(80) NOT NULL,
                    secondary_cta_url VARCHAR(255) NOT NULL,
                    featured_product_ids TEXT NOT NULL,
                    show_solutions TINYINT(1) NOT NULL DEFAULT 1,
                    show_company TINYINT(1) NOT NULL DEFAULT 1,
                    show_location TINYINT(1) NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS site_home_news (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    label VARCHAR(80) NOT NULL DEFAULT 'NOVIDADE',
                    title VARCHAR(180) NOT NULL,
                    body TEXT NOT NULL,
                    link_label VARCHAR(80) NOT NULL DEFAULT '',
                    link_url VARCHAR(255) NOT NULL DEFAULT '',
                    active TINYINT(1) NOT NULL DEFAULT 1,
                    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_site_home_news_active_order (active, sort_order, id)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                "SELECT id FROM site_home_config WHERE id = 1 LIMIT 1"
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO site_home_config (
                        id,
                        announcement_active,
                        announcement_label,
                        announcement_text,
                        announcement_link_label,
                        announcement_link_url,
                        hero_kicker,
                        hero_title,
                        hero_summary,
                        primary_cta_label,
                        primary_cta_url,
                        secondary_cta_label,
                        secondary_cta_url,
                        featured_product_ids,
                        show_solutions,
                        show_company,
                        show_location
                    )
                    VALUES (
                        1, 0, 'AVISO', '', '', '',
                        %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, 1
                    )
                    """,
                    (
                        default_config["hero_kicker"],
                        default_config["hero_title"],
                        default_config["hero_summary"],
                        default_config["primary_cta_label"],
                        default_config["primary_cta_url"],
                        default_config["secondary_cta_label"],
                        default_config["secondary_cta_url"],
                        json.dumps(
                            _decode_featured_ids(featured_product_ids or []),
                            ensure_ascii=False,
                        ),
                    ),
                )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise _database_error(exc, "schema initialization") from exc
    finally:
        connection.close()


def get_home_config():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    announcement_active,
                    announcement_label,
                    announcement_text,
                    announcement_link_label,
                    announcement_link_url,
                    hero_kicker,
                    hero_title,
                    hero_summary,
                    primary_cta_label,
                    primary_cta_url,
                    secondary_cta_label,
                    secondary_cta_url,
                    featured_product_ids,
                    show_solutions,
                    show_company,
                    show_location,
                    updated_at
                FROM site_home_config
                WHERE id = 1
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row is None:
                raise HomeContentNotInitialized(
                    "A configuração principal da Home ainda não existe."
                )
            return _hydrate_config(row)
    except HomeContentNotInitialized:
        raise
    except Exception as exc:
        raise _database_error(exc, "config lookup") from exc
    finally:
        connection.close()


def update_home_config(data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE site_home_config
                SET
                    announcement_active = %s,
                    announcement_label = %s,
                    announcement_text = %s,
                    announcement_link_label = %s,
                    announcement_link_url = %s,
                    hero_kicker = %s,
                    hero_title = %s,
                    hero_summary = %s,
                    primary_cta_label = %s,
                    primary_cta_url = %s,
                    secondary_cta_label = %s,
                    secondary_cta_url = %s,
                    featured_product_ids = %s,
                    show_solutions = %s,
                    show_company = %s,
                    show_location = %s
                WHERE id = 1
                """,
                (
                    1 if data["announcement_active"] else 0,
                    data["announcement_label"],
                    data["announcement_text"],
                    data["announcement_link_label"],
                    data["announcement_link_url"],
                    data["hero_kicker"],
                    data["hero_title"],
                    data["hero_summary"],
                    data["primary_cta_label"],
                    data["primary_cta_url"],
                    data["secondary_cta_label"],
                    data["secondary_cta_url"],
                    json.dumps(
                        _decode_featured_ids(data["featured_product_ids"]),
                        ensure_ascii=False,
                    ),
                    1 if data["show_solutions"] else 0,
                    1 if data["show_company"] else 0,
                    1 if data["show_location"] else 0,
                ),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM site_home_config WHERE id = 1 LIMIT 1"
                )
                if cursor.fetchone() is None:
                    raise HomeContentNotInitialized(
                        "A configuração principal da Home ainda não existe."
                    )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, HomeContentNotInitialized):
            raise
        raise _database_error(exc, "config update") from exc
    finally:
        connection.close()


def list_home_news(active_only=False):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT
                    id,
                    label,
                    title,
                    body,
                    link_label,
                    link_url,
                    active,
                    sort_order,
                    created_at,
                    updated_at
                FROM site_home_news
            """
            if active_only:
                sql += " WHERE active = 1"
            sql += " ORDER BY sort_order ASC, id DESC"
            cursor.execute(sql)
            return list(cursor.fetchall())
    except Exception as exc:
        raise _database_error(exc, "news query") from exc
    finally:
        connection.close()


def get_home_news(news_id):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    label,
                    title,
                    body,
                    link_label,
                    link_url,
                    active,
                    sort_order,
                    created_at,
                    updated_at
                FROM site_home_news
                WHERE id = %s
                LIMIT 1
                """,
                (news_id,),
            )
            return cursor.fetchone()
    except Exception as exc:
        raise _database_error(exc, "news lookup") from exc
    finally:
        connection.close()


def create_home_news(data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO site_home_news (
                    label,
                    title,
                    body,
                    link_label,
                    link_url,
                    active,
                    sort_order
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["label"],
                    data["title"],
                    data["body"],
                    data["link_label"],
                    data["link_url"],
                    1 if data["active"] else 0,
                    data["sort_order"],
                ),
            )
            news_id = cursor.lastrowid
        connection.commit()
        return news_id
    except Exception as exc:
        connection.rollback()
        raise _database_error(exc, "news insert") from exc
    finally:
        connection.close()


def update_home_news(news_id, data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE site_home_news
                SET
                    label = %s,
                    title = %s,
                    body = %s,
                    link_label = %s,
                    link_url = %s,
                    active = %s,
                    sort_order = %s
                WHERE id = %s
                """,
                (
                    data["label"],
                    data["title"],
                    data["body"],
                    data["link_label"],
                    data["link_url"],
                    1 if data["active"] else 0,
                    data["sort_order"],
                    news_id,
                ),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM site_home_news WHERE id = %s LIMIT 1",
                    (news_id,),
                )
                if cursor.fetchone() is None:
                    raise HomeContentError("Novidade não encontrada.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, HomeContentError):
            raise
        raise _database_error(exc, "news update") from exc
    finally:
        connection.close()


def set_home_news_active(news_id, active):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE site_home_news SET active = %s WHERE id = %s",
                (1 if active else 0, news_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM site_home_news WHERE id = %s LIMIT 1",
                    (news_id,),
                )
                if cursor.fetchone() is None:
                    raise HomeContentError("Novidade não encontrada.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, HomeContentError):
            raise
        raise _database_error(exc, "news status update") from exc
    finally:
        connection.close()
