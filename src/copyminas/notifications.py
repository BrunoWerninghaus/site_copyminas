import smtplib
from email.message import EmailMessage
from html import escape

from flask import current_app

from src.copyminas.contact import COPY_MINAS_CONTACT


class ContactNotificationError(RuntimeError):
    pass


def _safe(value):
    return escape(str(value), quote=True)


def _email_shell(*, eyebrow, title, intro, content, footer_note):
    phones = " · ".join(phone["display"] for phone in COPY_MINAS_CONTACT["phones"])
    return f"""<!doctype html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background:#090d12;color:#151515;font-family:'Courier New',Courier,monospace;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#090d12;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:680px;border-collapse:collapse;">
          <tr>
            <td style="padding:0 0 14px 0;color:#ffffff;font-size:13px;font-weight:700;letter-spacing:2px;">
              COPY MINAS <span style="color:#d51b29;">/</span> ELÓI MENDES · MG
            </td>
          </tr>
          <tr>
            <td style="background:#f5f1e8;border-top:5px solid #d51b29;border-right:1px solid #c9c2b6;border-bottom:1px solid #c9c2b6;border-left:1px solid #c9c2b6;padding:30px;">
              <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#777066;margin-bottom:18px;">{eyebrow}</div>
              <h1 style="margin:0;font-family:'Courier New',Courier,monospace;font-size:28px;line-height:1.08;letter-spacing:-1px;text-transform:uppercase;color:#111820;">{title}</h1>
              <p style="margin:18px 0 0 0;font-size:14px;line-height:1.75;color:#4e4a44;">{intro}</p>
              <div style="margin-top:26px;border-top:1px solid #c9c2b6;padding-top:24px;">
                {content}
              </div>
            </td>
          </tr>
          <tr>
            <td style="background:#111820;border-left:4px solid #1595ff;padding:18px 20px;color:#c8d1d8;">
              <div style="font-size:11px;line-height:1.7;letter-spacing:.3px;">{footer_note}</div>
              <div style="margin-top:8px;font-size:11px;line-height:1.7;color:#8f9aa3;">
                {phones} · copyminas@hotmail.com
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _row(label, value):
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-bottom:1px solid #d8d1c5;">
  <tr>
    <td style="width:38%;padding:10px 8px 10px 0;font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#777066;vertical-align:top;">{_safe(label)}</td>
    <td style="padding:10px 0;font-size:13px;line-height:1.55;color:#111820;vertical-align:top;overflow-wrap:anywhere;">{_safe(value)}</td>
  </tr>
</table>"""


def _message_block(text):
    return f"""
<div style="margin-top:20px;background:#ffffff;border:1px solid #c9c2b6;padding:16px;">
  <div style="font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#777066;margin-bottom:9px;">Mensagem</div>
  <div style="font-size:13px;line-height:1.7;color:#111820;white-space:pre-wrap;">{_safe(text)}</div>
</div>"""


def _build_internal_message(protocol, data, sender, recipient, service_label, preference_label):
    quantity = data.get("equipment_quantity")
    company = data.get("company") or "Não informada"

    message = EmailMessage()
    message["Subject"] = f"[Copy Minas] Novo contato {protocol} — {service_label}"
    message["From"] = f"Copy Minas | Site <{sender}>"
    message["To"] = recipient
    message["Reply-To"] = data["email"]

    message.set_content(
        "\n".join(
            [
                "COPY MINAS / NOVA SOLICITAÇÃO",
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

    rows = "".join(
        [
            _row("Protocolo", protocol),
            _row("Nome", data["name"]),
            _row("Empresa", company),
            _row("E-mail", data["email"]),
            _row("Telefone", data["phone"]),
            _row("Cidade", data["city"]),
            _row("Serviço", service_label),
            _row("Quantidade", quantity if quantity is not None else "Não informada"),
            _row("Preferência", preference_label),
        ]
    )

    message.add_alternative(
        _email_shell(
            eyebrow="SITE / NOVA SOLICITAÇÃO",
            title="Novo contato recebido.",
            intro="Uma nova solicitação foi registrada pelo formulário público da Copy Minas.",
            content=rows + _message_block(data["message"]),
            footer_note="REGISTRO INTERNO · origem: site · status inicial: novo",
        ),
        subtype="html",
    )
    return message


def _build_customer_message(protocol, data, sender, service_label):
    message = EmailMessage()
    message["Subject"] = f"Recebemos sua solicitação — Copy Minas | {protocol}"
    message["From"] = f"Copy Minas <{sender}>"
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

    protocol_box = f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:18px;background:#111820;border-left:4px solid #1595ff;">
  <tr>
    <td style="padding:16px 18px;">
      <div style="font-size:10px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:#91a1ad;">Protocolo de atendimento</div>
      <div style="margin-top:7px;font-size:19px;font-weight:700;letter-spacing:.7px;color:#ffffff;overflow-wrap:anywhere;">{_safe(protocol)}</div>
    </td>
  </tr>
</table>"""

    content = (
        protocol_box
        + _row("Serviço solicitado", service_label)
        + _message_block(data["message"])
        + """
<p style="margin:22px 0 0 0;font-size:13px;line-height:1.7;color:#4e4a44;">
  Nossa equipe recebeu seus dados e poderá entrar em contato pelos canais informados no formulário.
  Guarde este e-mail para consultar seu protocolo quando precisar falar conosco.
</p>"""
    )

    message.add_alternative(
        _email_shell(
            eyebrow="CONFIRMAÇÃO DE CONTATO",
            title=f"Olá, {_safe(data['name'])}.",
            intro="Recebemos sua solicitação e ela já está registrada para atendimento.",
            content=content,
            footer_note="COPY MINAS · impressão, tecnologia e equipamentos para o trabalho.",
        ),
        subtype="html",
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
