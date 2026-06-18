"""Entry point. Run with:  python run.py  (or via gunicorn in production)."""
import os
from app import create_app, db

app = create_app()

# Create DB tables on first boot (safe to run repeatedly)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)