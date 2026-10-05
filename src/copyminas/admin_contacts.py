import pymysql

from src.copyminas.db import DatabaseUnavailable, open_database


class AdminContactError(RuntimeError):
    pass


CONTACT_STATUSES = (
    "novo",
    "em_atendimento",
    "convertido",
    "encerrado",
    "spam",
)

CONTACT_STATUS_LABELS = {
    "novo": "Novo",
    "em_atendimento": "Em atendimento",
    "convertido": "Convertido",
    "encerrado": "Encerrado",
    "spam": "Spam",
}

CONTACT_SERVICE_LABELS = {
    "locacao_impressora": "Locação de impressora",
    "locacao_computador": "Locação de computador",
    "manutencao_impressora": "Manutenção de impressora",
    "manutencao_computador": "Manutenção de computador",
    "suporte": "Suporte",
    "outro": "Outro",
}

CONTACT_PREFERENCE_LABELS = {
    "whatsapp": "WhatsApp",
    "telefone": "Telefone",
    "email": "E-mail",
}


def _database_error(exc, action):
    if isinstance(exc, DatabaseUnavailable):
        return exc

    if isinstance(exc, pymysql.MySQLError):
        code = exc.args[0] if exc.args else "unknown"
        detail = exc.args[1] if len(exc.args) > 1 else str(exc)
        return DatabaseUnavailable(
            f"MySQL main_bd contact {action} failed [{code}]: {detail}"
        )

    return AdminContactError(f"Contact admin {action} failed: {exc}")


def list_contacts():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    protocol,
                    name,
                    company,
                    email,
                    phone,
                    city,
                    service_type,
                    equipment_quantity,
                    preferred_contact,
                    message,
                    consent_privacy,
                    consent_at,
                    status,
                    source,
                    created_at,
                    updated_at
                FROM contatos
                ORDER BY created_at DESC, id DESC
                """
            )
            return list(cursor.fetchall())
    except Exception as exc:
        raise _database_error(exc, "list query") from exc
    finally:
        connection.close()


def get_contact(contact_id):
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    protocol,
                    name,
                    company,
                    email,
                    phone,
                    city,
                    service_type,
                    equipment_quantity,
                    preferred_contact,
                    message,
                    consent_privacy,
                    consent_at,
                    status,
                    source,
                    created_at,
                    updated_at
                FROM contatos
                WHERE id = %s
                LIMIT 1
                """,
                (contact_id,),
            )
            return cursor.fetchone()
    except Exception as exc:
        raise _database_error(exc, "lookup") from exc
    finally:
        connection.close()


def contact_summary():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN status = 'novo' THEN 1 ELSE 0 END), 0) AS novos,
                    COALESCE(SUM(CASE WHEN status = 'em_atendimento' THEN 1 ELSE 0 END), 0) AS em_atendimento,
                    COALESCE(SUM(CASE WHEN status = 'convertido' THEN 1 ELSE 0 END), 0) AS convertidos
                FROM contatos
                """
            )
            return cursor.fetchone() or {
                "total": 0,
                "novos": 0,
                "em_atendimento": 0,
                "convertidos": 0,
            }
    except Exception as exc:
        raise _database_error(exc, "summary query") from exc
    finally:
        connection.close()


def update_contact_status(contact_id, status):
    if status not in CONTACT_STATUSES:
        raise AdminContactError("Status de contato inválido.")

    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE contatos
                SET status = %s
                WHERE id = %s
                """,
                (status, contact_id),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM contatos WHERE id = %s LIMIT 1",
                    (contact_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminContactError("Contato não encontrado.")

        connection.commit()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, AdminContactError):
            raise
        raise _database_error(exc, "status update") from exc
    finally:
        connection.close()
