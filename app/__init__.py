"""Aether AI – application factory."""
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from markupsafe import Markup
import markdown as md

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app():
    from .config import Config
    from werkzeug.middleware.proxy_fix import ProxyFix  # ← ADD THIS

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # Trust Render's reverse proxy for HTTPS detection
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # ← ADD THIS

    db.init_app(app)
    ...
    login_manager.init_app(app)

    # ---- Markdown filter (renders AI output as nice HTML) ----
    md_ext = ["fenced_code", "tables", "sane_lists", "nl2br"]
    @app.template_filter("md")
    def render_markdown(text):
        if not text:
            return ""
        html = md.markdown(text, extensions=md_ext)
        return Markup(html)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.notes import notes_bp
    from .routes.flashcards import flashcards_bp
    from .routes.quizzes import quizzes_bp
    from .routes.chat import chat_bp
    from .routes.planner import planner_bp
    from .routes.rooms import rooms_bp
    from .routes.pdf import pdf_bp
    from .routes.wikipedia import wikipedia_bp


    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(flashcards_bp, url_prefix="/decks")
    app.register_blueprint(quizzes_bp, url_prefix="/study")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(planner_bp, url_prefix="/planner")
    app.register_blueprint(rooms_bp, url_prefix="/rooms")
    app.register_blueprint(pdf_bp, url_prefix="/pdf")
    app.register_blueprint(wikipedia_bp, url_prefix="/wikipedia")
    @app.context_processor
    def inject_brand():
        cfg = app.config
        pref = (cfg.get("AI_PROVIDER") or "groq").lower()
        if pref == "groq" and not cfg.get("GROQ_API_KEY"):
            pref = "gemini" if cfg.get("GEMINI_API_KEY") else "mock"
        elif pref == "gemini" and not cfg.get("GEMINI_API_KEY"):
            pref = "groq" if cfg.get("GROQ_API_KEY") else "mock"
        return {
            "BRAND": "Aether AI",
            "TAGLINE": "Learn smarter, not harder.",
            "AI_PROVIDER_NAME": pref,
        }

    return app