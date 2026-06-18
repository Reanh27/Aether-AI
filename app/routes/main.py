"""Landing/marketing pages."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    # Logged in → dashboard. Logged out → login page.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@main_bp.route("/welcome")
def welcome():
    """Public marketing/landing page (the old home)."""
    return render_template("home.html", user=current_user)


@main_bp.route("/about")
def about():
    return render_template("about.html")