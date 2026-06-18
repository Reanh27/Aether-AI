"""Central configuration loaded from environment variables."""
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///aether.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Choose: groq | gemini | mock
    AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")

    # Groq (recommended — fast + free, 30 req/min)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Gemini (backup)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Wikipedia (no key required)
    WIKI_USER_AGENT = "AetherAI/1.0 (educational study assistant)"
        # ---- Email (SMTP) ----
    MAIL_BACKEND = os.getenv("MAIL_BACKEND", "console")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Aether AI")