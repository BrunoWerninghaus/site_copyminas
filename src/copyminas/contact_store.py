from datetime import datetime
from secrets import token_hex

import pymysql

from src.copyminas.db import DatabaseUnavailable, open_database


def generate_contact_protocol():
    # 2 + 6 + 12 = 20 characters, matching contatos.protocol varchar(20).
    return f"CM{datetime.now():%y%m%d}{token_hex(6).upper()}"


def create_contact_request(data):
    protocol = generate_contact_protocol()
    connection = open_database()

    sql = """
        INSERT INTO contatos (
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
            consent_privacy
        )
        VALUES (
            %(protocol)s,
            %(name)s,
            %(company)s,
            %(email)s,
            %(phone)s,
            %(city)s,
            %(service_type)s,
            %(equipment_quantity)s,
            %(preferred_contact)s,
            %(message)s,
            %(consent_privacy)s
        )
    """

    payload = {
        **data,
        "protocol": protocol,
        "company": data.get("company") or None,
        "equipment_quantity": data.get("equipment_quantity") or None,
        "consent_privacy": 1,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, payload)
        connection.commit()
    except pymysql.MySQLError as exc:
        connection.rollback()
        raise DatabaseUnavailable(
            "Could not persist the contact request in main_bd.contatos."
        ) from exc
    finally:
        connection.close()

    return protocol
