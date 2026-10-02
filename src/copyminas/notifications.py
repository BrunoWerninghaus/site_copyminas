import smtplib
from email.message import EmailMessage

from flask import current_app


class ContactNotificationError(RuntimeError):
    pass


def _build_internal_message(protocol, data, sender, recipient, service_label, preference_label):
    quantity = data.get("equipment_quantity")
    company = data.get("company") or "Não informada"

    message = EmailMessage()
    message["Subject"] = f"[Copy Minas] Novo contato {protocol} — {service_label}"
    message["From"] = sender
    message["To"] = recipient
    message["Reply-To"] = data["email"]
    message.set_content(
        "\n".join(
            [
                "Nova solicitação recebida pelo site Copy Minas.",
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
    return message


def _build_customer_message(protocol, data, sender, service_label):
    message = EmailMessage()
    message["Subject"] = f"Recebemos sua solicitação — Copy Minas | {protocol}"
    message["From"] = sender
    message["To"] = data["email"]
    message["Reply-To"] = sender
    message.set_content(
        "\n".join(
            [
                f"Olá, {data['name']}.",
                "",
                "Recebemos sua solicitação pelo site da Copy Minas.",
                "",
                f"Protocolo de atendimento: {protocol}",
                f"Serviço solicitado: {service_label}",
                "",
                "Sua mensagem foi registrada e nossa equipe poderá entrar em contato "
                "pelos dados informados no formulário.",
                "",
                "Mensagem recebida:",
                data["message"],
                "",
                "Copy Minas",
                "Elói Mendes - MG",
            ]
        )
    )
    return message


def send_contact_notifications(protocol, data):
    host = current_app.config.get("SMTP_HOST", "").strip()
    if not host:
        raise ContactNotificationError("SMTP_HOST is not configured.")

    sender = current_app.config["CONTACT_NOTIFICATION_FROM"]
    internal_recipient = current_app.config["CONTACT_NOTIFICATION_TO"]

    service_label = current_app.config["CONTACT_SERVICE_LABELS"].get(
        data["service_type"],
        data["service_type"],
    )
    preference_label = current_app.config["CONTACT_PREFERENCE_LABELS"].get(
        data["preferred_contact"],
        data["preferred_contact"],
    )

    internal_message = _build_internal_message(
        protocol,
        data,
        sender,
        internal_recipient,
        service_label,
        preference_label,
    )
    customer_message = _build_customer_message(
        protocol,
        data,
        sender,
        service_label,
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

            smtp.send_message(internal_message)
            smtp.send_message(customer_message)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        raise ContactNotificationError(
            f"SMTP notification failed: {exc}"
        ) from exc
