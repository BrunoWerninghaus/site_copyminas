import re

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from src.copyminas.catalog import (
    get_product_by_slug,
    get_public_categories,
    get_public_products,
)
from src.copyminas.company import COPY_MINAS_COMPANY
from src.copyminas.contact import COPY_MINAS_CONTACT
from src.copyminas.contact_store import create_contact_request
from src.copyminas.db import DatabaseUnavailable
from src.copyminas.location import COPY_MINAS_LOCATION
from src.copyminas.notifications import (
    ContactNotificationError,
    send_contact_notifications,
)


public_bp = Blueprint("public", __name__)

CONTACT_SERVICE_TYPES = (
    ("locacao_impressora", "Locação de impressora"),
    ("locacao_computador", "Locação de computador"),
    ("manutencao_impressora", "Manutenção de impressora"),
    ("manutencao_computador", "Manutenção de computador"),
    ("suporte", "Suporte"),
    ("outro", "Outro"),
)

CONTACT_PREFERENCES = (
    ("whatsapp", "WhatsApp"),
    ("telefone", "Telefone"),
    ("email", "E-mail"),
)


def _contact_label_maps():
    return (
        dict(CONTACT_SERVICE_TYPES),
        dict(CONTACT_PREFERENCES),
    )


@public_bp.get("/")
def intro():
    return render_template(
        "public/intro.html",
        copyminas_location=COPY_MINAS_LOCATION,
    )


@public_bp.get("/home")
def home():
    return render_template(
        "public/home.html",
        company=COPY_MINAS_COMPANY,
        copyminas_location=COPY_MINAS_LOCATION,
        featured_products=get_public_products(limit=3),
    )


@public_bp.get("/solucoes")
def solutions():
    return render_template(
        "public/solutions.html",
        company=COPY_MINAS_COMPANY,
    )


@public_bp.get("/empresa")
def company():
    return render_template(
        "public/company.html",
        company=COPY_MINAS_COMPANY,
        copyminas_location=COPY_MINAS_LOCATION,
    )


@public_bp.get("/produtos")
def products():
    return render_template(
        "public/products.html",
        products=get_public_products(),
        categories=get_public_categories(),
    )


@public_bp.get("/produtos/<slug>")
def product_detail(slug):
    product = get_product_by_slug(slug)

    if product is None:
        abort(404)

    return render_template(
        "public/product_detail.html",
        product=product,
    )


def _render_contact(*, form_data=None, form_errors=None, status=200):
    return (
        render_template(
            "public/contact.html",
            contact=COPY_MINAS_CONTACT,
            copyminas_location=COPY_MINAS_LOCATION,
            contact_service_types=CONTACT_SERVICE_TYPES,
            contact_preferences=CONTACT_PREFERENCES,
            form_data=form_data or {},
            form_errors=form_errors or [],
        ),
        status,
    )


@public_bp.get("/contato")
def contact():
    return _render_contact()


@public_bp.post("/contato/enviar")
def contact_submit():
    fields = (
        "name",
        "company",
        "email",
        "phone",
        "city",
        "service_type",
        "equipment_quantity",
        "preferred_contact",
        "message",
    )
    form_data = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    errors = []

    if not form_data["name"]:
        errors.append("Informe seu nome.")
    elif len(form_data["name"]) < 2:
        errors.append("Informe um nome com pelo menos 2 caracteres.")
    elif len(form_data["name"]) > 120:
        errors.append("O nome deve ter no máximo 120 caracteres.")

    if len(form_data["company"]) > 160:
        errors.append("O nome da empresa deve ter no máximo 160 caracteres.")

    if not form_data["email"] or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        form_data["email"],
    ):
        errors.append("Informe um e-mail válido.")
    elif len(form_data["email"]) > 254:
        errors.append("O e-mail deve ter no máximo 254 caracteres.")

    if not form_data["phone"]:
        errors.append("Informe um telefone ou WhatsApp.")
    elif len(form_data["phone"]) > 20:
        errors.append("O telefone deve ter no máximo 20 caracteres.")
    else:
        phone_digits = re.sub(r"\D", "", form_data["phone"])
        if not 8 <= len(phone_digits) <= 15:
            errors.append("Informe um telefone válido, com DDD quando aplicável.")

    if not form_data["city"]:
        errors.append("Informe sua cidade.")
    elif len(form_data["city"]) < 2:
        errors.append("Informe uma cidade válida.")
    elif len(form_data["city"]) > 120:
        errors.append("A cidade deve ter no máximo 120 caracteres.")

    service_keys = {key for key, _ in CONTACT_SERVICE_TYPES}
    if form_data["service_type"] not in service_keys:
        errors.append("Selecione um tipo de serviço válido.")

    preference_keys = {key for key, _ in CONTACT_PREFERENCES}
    if form_data["preferred_contact"] not in preference_keys:
        errors.append("Selecione uma preferência de contato válida.")

    quantity = None
    if form_data["equipment_quantity"]:
        try:
            quantity = int(form_data["equipment_quantity"])
        except ValueError:
            errors.append("A quantidade de equipamentos deve ser um número inteiro.")
        else:
            if quantity < 1 or quantity > 65535:
                errors.append("A quantidade de equipamentos deve estar entre 1 e 65535.")

    if not form_data["message"]:
        errors.append("Escreva uma mensagem.")
    elif len(form_data["message"]) < 8:
        errors.append("Escreva uma mensagem com pelo menos 8 caracteres.")
    elif len(form_data["message"]) > 5000:
        errors.append("A mensagem deve ter no máximo 5000 caracteres.")

    if request.form.get("consent_privacy") != "1":
        errors.append("Confirme o consentimento para registrar a solicitação.")

    form_data["equipment_quantity"] = quantity

    if errors:
        return _render_contact(
            form_data=form_data,
            form_errors=errors,
            status=422,
        )

    try:
        protocol = create_contact_request(form_data)
    except DatabaseUnavailable as exc:
        current_app.logger.error("Contact persistence failed: %s", exc)
        return _render_contact(
            form_data=form_data,
            form_errors=[
                "Não foi possível registrar a solicitação no momento. "
                "Use um dos canais diretos ao lado."
            ],
            status=503,
        )

    service_labels, preference_labels = _contact_label_maps()
    current_app.config["CONTACT_SERVICE_LABELS"] = service_labels
    current_app.config["CONTACT_PREFERENCE_LABELS"] = preference_labels

    confirmation_sent = True
    try:
        send_contact_notifications(protocol, form_data)
    except ContactNotificationError as exc:
        confirmation_sent = False
        current_app.logger.error(
            "Contact %s persisted, but email notification failed: %s",
            protocol,
            exc,
        )

    if confirmation_sent:
        flash(
            "Solicitação recebida. Enviamos uma confirmação para o e-mail informado.",
            "contact-success",
        )
    else:
        flash(
            "Solicitação recebida. Não foi possível enviar a confirmação por e-mail neste momento.",
            "contact-warning",
        )
    return redirect(url_for("public.contact"), code=303)
