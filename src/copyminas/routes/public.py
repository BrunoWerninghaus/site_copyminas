from flask import Blueprint, render_template


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def intro():
    return render_template("public/intro.html")


@public_bp.get("/home")
def home():
    return render_template("public/home.html")
