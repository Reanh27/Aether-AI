"""Dashboard – stats + weekly activity chart."""
from datetime import datetime, timedelta
from collections import OrderedDict
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import Note, Deck, Quiz, StudyRoom, StudyActivity, PlanItem, StudyPlan

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    uid = current_user.id

    total_decks = Deck.query.filter_by(user_id=uid).count()
    cards_studied = StudyActivity.query.filter_by(user_id=uid, kind="card").count()
    active_rooms = StudyRoom.query.filter_by(user_id=uid, active=True).count()
    upcoming = (PlanItem.query
                .join(StudyPlan, PlanItem.plan_id == StudyPlan.id)
                .filter(StudyPlan.user_id == uid, PlanItem.done == False)
                .count())

    quizzes = Quiz.query.filter_by(user_id=uid).filter(Quiz.score.isnot(None)).all()
    if quizzes:
        total_qs = sum(len(q.questions) for q in quizzes) or 1
        scored = sum(q.score for q in quizzes)
        accuracy = int(round((scored / total_qs) * 100))
    else:
        accuracy = 0

    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    counts = OrderedDict((d, 0) for d in labels)
    week_end = monday + timedelta(days=7)
    acts = (StudyActivity.query
            .filter(StudyActivity.user_id == uid,
                    StudyActivity.created_at >= monday,
                    StudyActivity.created_at < week_end)
            .all())
    for a in acts:
        idx = (a.created_at.date() - monday).days
        if 0 <= idx < 7:
            counts[labels[idx]] += 1

    recent_decks = (Deck.query.filter_by(user_id=uid)
                    .order_by(Deck.created_at.desc()).limit(4).all())

    return render_template(
        "dashboard.html",
        total_decks=total_decks, cards_studied=cards_studied,
        active_rooms=active_rooms, upcoming=upcoming, accuracy=accuracy,
        chart_labels=list(counts.keys()), chart_values=list(counts.values()),
        recent_decks=recent_decks,
    )