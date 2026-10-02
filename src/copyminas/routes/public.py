from urllib.parse import urlencode

from flask import Blueprint, abort, redirect, render_template, request

from src.copyminas.catalog import (
    get_product_by_slug,
    get_public_categories,
    get_public_products,
)
from src.copyminas.company import COPY_MINAS_COMPANY
from src.copyminas.contact import COPY_MINAS_CONTACT
from src.copyminas.location import COPY_MINAS_LOCATION


public_bp = Blueprint("public", __name__)

CONTACT_SUBJECTS = (
    "Orçamento",
    "Produtos",
    "Suporte / manutenção",
    "Locação",
    "Outro assunto",
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
            contact_subjects=CONTACT_SUBJECTS,
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
    fields = ("name", "company", "reply", "subject", "message")
    form_data = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    errors = []

    if not form_data["name"]:
        errors.append("Informe seu nome.")
    elif len(form_data["name"]) > 120:
        errors.append("O nome deve ter no máximo 120 caracteres.")

    if not form_data["reply"]:
        errors.append("Informe um telefone, WhatsApp ou e-mail para retorno.")
    elif len(form_data["reply"]) > 160:
        errors.append("O contato de retorno deve ter no máximo 160 caracteres.")

    if form_data["subject"] not in CONTACT_SUBJECTS:
        errors.append("Selecione um assunto válido.")

    if not form_data["message"]:
        errors.append("Escreva uma mensagem.")
    elif len(form_data["message"]) > 2000:
        errors.append("A mensagem deve ter no máximo 2000 caracteres.")

    if len(form_data["company"]) > 160:
        errors.append("O nome da empresa deve ter no máximo 160 caracteres.")

    target_raw = request.form.get("target", "0")
    try:
        target_index = int(target_raw)
    except ValueError:
        target_index = 0

    if target_index < 0 or target_index >= len(COPY_MINAS_CONTACT["phones"]):
        target_index = 0

    if errors:
        return _render_contact(
            form_data=form_data,
            form_errors=errors,
            status=422,
        )

    message_lines = [
        "Olá, Copy Minas.",
        "",
        f"Nome: {form_data['name']}",
    ]

    if form_data["company"]:
        message_lines.append(f"Empresa: {form_data['company']}")

    message_lines.extend(
        [
            f"Retorno: {form_data['reply']}",
            f"Assunto: {form_data['subject']}",
            "",
            form_data["message"],
        ]
    )

    whatsapp = COPY_MINAS_CONTACT["phones"][target_index]["whatsapp"]
    query = urlencode({"text": "\n".join(message_lines)})

    return redirect(f"{whatsapp}?{query}", code=303)
