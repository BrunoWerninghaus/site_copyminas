from flask import Blueprint, render_template

from src.copyminas.catalog import get_public_products
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
        copyminas_location=COPY_MINAS_LOCATION,
        featured_products=get_public_products(limit=3),
    )


@public_bp.get("/produtos")
def products():
    return render_template(
        "public/products.html",
        products=get_public_products(),
    )


@public_bp.get("/contato")
def contact():
    return render_template(
        "public/contact.html",
        contact=COPY_MINAS_CONTACT,
        copyminas_location=COPY_MINAS_LOCATION,
    )
