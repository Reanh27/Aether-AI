"""Wikipedia Search — free, unlimited knowledge from Wikipedia REST API."""
from flask import Blueprint, render_template, request
from flask_login import login_required
from ..services import wiki

wikipedia_bp = Blueprint("wikipedia", __name__)


@wikipedia_bp.route("/")
@login_required
def index():
    query = (request.args.get("q") or "").strip()
    results = []
    featured = None
    if query:
        featured = wiki.summary(query)
        if featured and not featured.get("extract"):
            featured = None
        results = wiki.search(query, limit=8)
        if featured and results and results[0].get("title", "").lower() == featured.get("title", "").lower():
            results = results[1:]
    return render_template("wikipedia/index.html",
                           query=query, featured=featured, results=results)


@wikipedia_bp.route("/article/<path:title>")
@login_required
def article(title):
    data = wiki.summary(title)
    related = wiki.search(title, limit=6) if data else []
    return render_template("wikipedia/article.html",
                           data=data, title=title, related=related)