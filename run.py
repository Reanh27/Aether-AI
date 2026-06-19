"""Entry point. Run with:  python run.py  (or via gunicorn)."""
import os
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    # Safe migration: add email_verified column if missing
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
        db.session.commit()
        print("✓ Added email_verified column to users table")
    except Exception:
        db.session.rollback()  # column already exists, that's fine

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)