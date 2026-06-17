"""Entry point. Run with:  python run.py  """
import webbrowser
import threading
from app import create_app, db

app = create_app()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Open browser 1 second after server starts
    threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)