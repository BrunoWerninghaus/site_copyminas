from flask import Blueprint, render_template

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
    )
