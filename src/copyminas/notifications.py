import smtplib
from email.message import EmailMessage

from flask import current_app


class ContactNotificationError(RuntimeError):
    pass


def send_contact_notification(protocol, data):
    host = current_app.config.get("SMTP_HOST", "").strip()
    if not host:
        raise ContactNotificationError("SMTP_HOST is not configured.")

    sender = current_app.config["CONTACT_NOTIFICATION_FROM"]
    recipient = current_app.config["CONTACT_NOTIFICATION_TO"]

    service_label = current_app.config["CONTACT_SERVICE_LABELS"].get(
        data["service_type"],
        data["service_type"],
    )
    preference_label = current_app.config["CONTACT_PREFERENCE_LABELS"].get(
        data["preferred_contact"],
        data["preferred_contact"],
    )

    message = EmailMessage()
    message["Subject"] = f"[Copy Minas] Novo contato {protocol} — {service_label}"
    message["From"] = sender
    message["To"] = recipient
    message["Reply-To"] = data["email"]

    quantity = data.get("equipment_quantity")
    company = data.get("company") or "Não informada"

    message.set_content(
        "\n".join(
            [
                "Nova solicitação registrada pelo site Copy Minas.",
                "",
                f"Protocolo: {protocol}",
                f"Nome: {data['name']}",
                f"Empresa: {company}",
                f"E-mail: {data['email']}",
                f"Telefone: {data['phone']}",
                f"Cidade: {data['city']}",
                f"Serviço: {service_label}",
                f"Quantidade: {quantity if quantity is not None else 'Não informada'}",
                f"Preferência de contato: {preference_label}",
                "",
                "Mensagem:",
                data["message"],
                "",
                "Origem: site",
                "Status inicial: novo",
            ]
        )
    )

    port = current_app.config["SMTP_PORT"]
    security = current_app.config["SMTP_SECURITY"]
    username = current_app.config.get("SMTP_USER", "")
    password = current_app.config.get("SMTP_PASSWORD", "")

    try:
        if security == "ssl":
            smtp = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            smtp = smtplib.SMTP(host, port, timeout=10)

        with smtp:
            if security == "starttls":
                smtp.starttls()

            if username:
                smtp.login(username, password)

            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise ContactNotificationError(
            f"SMTP notification failed: {exc}"
        ) from exc
