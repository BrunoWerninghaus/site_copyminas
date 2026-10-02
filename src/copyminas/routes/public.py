from flask import Blueprint, abort, render_template

from src.copyminas.catalog import (
    get_product_by_slug,
    get_public_categories,
    get_public_products,
)
from src.copyminas.company import COPY_MINAS_COMPANY
from src.copyminas.contact import COPY_MINAS_CONTACT
from src.copyminas.location import COPY_MINAS_LOCATION


public_bp = Blueprint("public", __name__)


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


@public_bp.get("/contato")
def contact():
    return render_template(
        "public/contact.html",
        contact=COPY_MINAS_CONTACT,
        copyminas_location=COPY_MINAS_LOCATION,
    )
