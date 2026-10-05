import pymysql

from src.copyminas.db import DatabaseUnavailable, open_database


class AdminCatalogError(RuntimeError):
    pass


def _database_error(exc, action):
    if isinstance(exc, DatabaseUnavailable):
        return exc

    if isinstance(exc, pymysql.MySQLError):
        code = exc.args[0] if exc.args else "unknown"
        detail = exc.args[1] if len(exc.args) > 1 else str(exc)
        return DatabaseUnavailable(
            f"MySQL main_bd {action} failed [{code}]: {detail}"
        )

    return AdminCatalogError(f"Catalog admin {action} failed: {exc}")


def list_categories():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.nome,
                    c.ativo,
                    COUNT(p.id) AS product_count,
                    COALESCE(SUM(CASE WHEN p.ativo = 1 THEN 1 ELSE 0 END), 0) AS active_product_count
                FROM categorias AS c
                LEFT JOIN produtos AS p
                    ON p.categoria_id = c.id
                GROUP BY c.id, c.nome, c.ativo
                ORDER BY c.nome ASC, c.id ASC
                """
            )
            return list(cursor.fetchall())
    except Exception as exc:
        raise _database_error(exc, "category query") from exc
    finally:
        connection.close()


def get_category(category_id):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.nome,
                    c.ativo,
                    COUNT(p.id) AS product_count,
                    COALESCE(SUM(CASE WHEN p.ativo = 1 THEN 1 ELSE 0 END), 0) AS active_product_count
                FROM categorias AS c
                LEFT JOIN produtos AS p
                    ON p.categoria_id = c.id
                WHERE c.id = %s
                GROUP BY c.id, c.nome, c.ativo
                LIMIT 1
                """,
                (category_id,),
            )
            return cursor.fetchone()
    except Exception as exc:
        raise _database_error(exc, "category lookup") from exc
    finally:
        connection.close()


def create_category(data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO categorias (nome, ativo)
                VALUES (%s, %s)
                """,
                (data["nome"], data["ativo"]),
            )
            category_id = cursor.lastrowid
        connection.commit()
        return category_id
    except Exception as exc:
        connection.rollback()
        raise _database_error(exc, "category insert") from exc
    finally:
        connection.close()


def update_category(category_id, data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE categorias
                SET nome = %s, ativo = %s
                WHERE id = %s
                """,
                (data["nome"], data["ativo"], category_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM categorias WHERE id = %s LIMIT 1",
                    (category_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminCatalogError("Categoria não encontrada.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "category update") from exc
    finally:
        connection.close()


def set_category_active(category_id, active):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE categorias SET ativo = %s WHERE id = %s",
                (1 if active else 0, category_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM categorias WHERE id = %s LIMIT 1",
                    (category_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminCatalogError("Categoria não encontrada.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "category status update") from exc
    finally:
        connection.close()


def list_products():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.descricao,
                    p.imagem1,
                    p.imagem2,
                    p.imagem3,
                    p.imagem4,
                    p.imagem5,
                    p.espec,
                    p.ativo,
                    p.qtd,
                    p.categoria_id,
                    c.nome AS categoria,
                    c.ativo AS categoria_ativa,
                    p.created_at,
                    p.updated_at
                FROM produtos AS p
                LEFT JOIN categorias AS c
                    ON c.id = p.categoria_id
                ORDER BY p.ativo DESC, c.nome ASC, p.nome ASC, p.id ASC
                """
            )
            return list(cursor.fetchall())
    except Exception as exc:
        raise _database_error(exc, "product query") from exc
    finally:
        connection.close()


def get_product(product_id):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.descricao,
                    p.imagem1,
                    p.imagem2,
                    p.imagem3,
                    p.imagem4,
                    p.imagem5,
                    p.espec,
                    p.ativo,
                    p.qtd,
                    p.categoria_id,
                    c.nome AS categoria,
                    c.ativo AS categoria_ativa,
                    p.created_at,
                    p.updated_at
                FROM produtos AS p
                LEFT JOIN categorias AS c
                    ON c.id = p.categoria_id
                WHERE p.id = %s
                LIMIT 1
                """,
                (product_id,),
            )
            return cursor.fetchone()
    except Exception as exc:
        raise _database_error(exc, "product lookup") from exc
    finally:
        connection.close()


def _category_exists(cursor, category_id):
    cursor.execute(
        "SELECT id FROM categorias WHERE id = %s LIMIT 1",
        (category_id,),
    )
    return cursor.fetchone() is not None


def create_product(data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            if not _category_exists(cursor, data["categoria_id"]):
                raise AdminCatalogError("A categoria selecionada não existe.")

            cursor.execute(
                """
                INSERT INTO produtos (
                    nome,
                    descricao,
                    imagem1,
                    imagem2,
                    imagem3,
                    imagem4,
                    imagem5,
                    espec,
                    ativo,
                    categoria_id,
                    qtd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["nome"],
                    data["descricao"],
                    data["imagem1"],
                    data["imagem2"],
                    data["imagem3"],
                    data["imagem4"],
                    data["imagem5"],
                    data["espec"],
                    data["ativo"],
                    data["categoria_id"],
                    data["qtd"],
                ),
            )
            product_id = cursor.lastrowid
        connection.commit()
        return product_id
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "product insert") from exc
    finally:
        connection.close()


def update_product(product_id, data):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            if not _category_exists(cursor, data["categoria_id"]):
                raise AdminCatalogError("A categoria selecionada não existe.")

            cursor.execute(
                """
                UPDATE produtos
                SET
                    nome = %s,
                    descricao = %s,
                    imagem1 = %s,
                    imagem2 = %s,
                    imagem3 = %s,
                    imagem4 = %s,
                    imagem5 = %s,
                    espec = %s,
                    ativo = %s,
                    categoria_id = %s,
                    qtd = %s
                WHERE id = %s
                """,
                (
                    data["nome"],
                    data["descricao"],
                    data["imagem1"],
                    data["imagem2"],
                    data["imagem3"],
                    data["imagem4"],
                    data["imagem5"],
                    data["espec"],
                    data["ativo"],
                    data["categoria_id"],
                    data["qtd"],
                    product_id,
                ),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM produtos WHERE id = %s LIMIT 1",
                    (product_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminCatalogError("Produto não encontrado.")

        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "product update") from exc
    finally:
        connection.close()



def update_product_image_slot(product_id, slot, relative_path):
    try:
        slot = int(slot)
    except (TypeError, ValueError) as exc:
        raise AdminCatalogError("Slot de imagem inválido.") from exc

    if slot not in range(1, 6):
        raise AdminCatalogError("Slot de imagem inválido.")

    column = f"imagem{slot}"
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE produtos SET {column} = %s WHERE id = %s",
                (relative_path, product_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM produtos WHERE id = %s LIMIT 1",
                    (product_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminCatalogError("Produto não encontrado.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "product image update") from exc
    finally:
        connection.close()

def set_product_active(product_id, active):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE produtos SET ativo = %s WHERE id = %s",
                (1 if active else 0, product_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM produtos WHERE id = %s LIMIT 1",
                    (product_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminCatalogError("Produto não encontrado.")
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminCatalogError):
            raise
        raise _database_error(exc, "product status update") from exc
    finally:
        connection.close()
