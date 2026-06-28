"""AI Chat — ChatGPT-style sessions."""
import markdown as md
from datetime import date, timedelta
from collections import OrderedDict
from flask import (Blueprint, render_template, request, jsonify, redirect,
                   url_for, abort)
from flask_login import login_required, current_user
from .. import db
from ..models import ChatSession, ChatMessage, StudyActivity
from ..services.ai_service import chat_reply

chat_bp = Blueprint("chat", __name__)

_MD_EXT = ["fenced_code", "tables", "sane_lists", "nl2br"]


def _group_sessions(sessions):
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    groups = OrderedDict([
        ("Today", []),
        ("Yesterday", []),
        ("Previous 7 days", []),
        ("Older", []),
    ])
    for s in sessions:
        d = s.created_at.date() if s.created_at else today
        if d == today:
            groups["Today"].append(s)
        elif d == yesterday:
            groups["Yesterday"].append(s)
        elif d > week_ago:
            groups["Previous 7 days"].append(s)
        else:
            groups["Older"].append(s)
    return OrderedDict((k, v) for k, v in groups.items() if v)


@chat_bp.route("/")
@login_required
def index():
    sessions = (ChatSession.query.filter_by(user_id=current_user.id)
                .order_by(ChatSession.created_at.desc()).all())
    sid = request.args.get("s", type=int)

    if sid:
        current = ChatSession.query.get_or_404(sid)
        if current.user_id != current_user.id:
            abort(403)
    elif sessions:
        return redirect(url_for("chat.index", s=sessions[0].id))
    else:
        s = ChatSession(user_id=current_user.id, title="New chat")
        db.session.add(s)
        db.session.commit()
        return redirect(url_for("chat.index", s=s.id))

    return render_template("chat.html",
                           grouped=_group_sessions(sessions),
                           current=current)


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
    return jsonify({"reply": answer,
                    "reply_html": md.markdown(answer, extensions=_MD_EXT),
                    "title": s.title})


@chat_bp.route("/<int:session_id>/regenerate", methods=["POST"])
@login_required
def regenerate(session_id):
    s = ChatSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    msgs = list(s.messages)
    if len(msgs) < 2 or msgs[-1].role != "assistant" or msgs[-2].role != "user":
        return jsonify({"error": "nothing to regenerate"}), 400
    db.session.delete(msgs[-1])
    user_msg = msgs[-2]
    history = [{"role": m.role, "content": m.content} for m in msgs[:-2]]
    answer = chat_reply(user_msg.content, history)
    db.session.add(ChatMessage(session_id=s.id, role="assistant", content=answer))
    db.session.commit()
    return jsonify({"reply": answer,
                    "reply_html": md.markdown(answer, extensions=_MD_EXT)})


@chat_bp.route("/<int:session_id>/rename", methods=["POST"])
@login_required
def rename(session_id):
    s = ChatSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    data = request.get_json(silent=True) or {}
    new_title = (data.get("title") or "").strip()[:200]
    if not new_title:
        return jsonify({"error": "empty title"}), 400
    s.title = new_title
    db.session.commit()
    return jsonify({"ok": True, "title": s.title})


@chat_bp.route("/<int:session_id>/delete", methods=["POST"])
@login_required
def delete(session_id):
    s = ChatSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("chat.index"))