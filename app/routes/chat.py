"""AI Chat with multiple conversation sessions (ChatGPT-style sidebar)."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
from .. import db
from ..models import ChatSession, ChatMessage, StudyActivity
from ..services.ai_service import chat_reply

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
@login_required
def index():
    sessions = (ChatSession.query.filter_by(user_id=current_user.id)
                .order_by(ChatSession.created_at.desc()).all())
    current = None
    sid = request.args.get("s", type=int)
    if sid:
        current = ChatSession.query.get_or_404(sid)
        if current.user_id != current_user.id:
            abort(403)
    elif sessions:
        current = sessions[0]
    return render_template("chat.html", sessions=sessions, current=current)


@chat_bp.route("/new", methods=["POST"])
@login_required
def new_session():
    s = ChatSession(user_id=current_user.id, title="New chat")
    db.session.add(s)
    db.session.commit()
    return redirect(url_for("chat.index", s=s.id))


@chat_bp.route("/<int:session_id>/send", methods=["POST"])
@login_required
def send(session_id):
    s = ChatSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty"}), 400

    if not s.messages:
        s.title = (message[:50] + ("…" if len(message) > 50 else ""))

    db.session.add(ChatMessage(session_id=s.id, role="user", content=message))
    history = [{"role": m.role, "content": m.content} for m in s.messages]
    answer = chat_reply(message, history)
    db.session.add(ChatMessage(session_id=s.id, role="assistant", content=answer))
    db.session.add(StudyActivity(user_id=current_user.id, kind="chat"))
    db.session.commit()

    import markdown as md
    answer_html = md.markdown(answer, extensions=["fenced_code", "tables",
                                                  "sane_lists", "nl2br"])
    return jsonify({"reply": answer, "reply_html": answer_html, "title": s.title})


@chat_bp.route("/<int:session_id>/delete", methods=["POST"])
@login_required
def delete(session_id):
    s = ChatSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("chat.index"))