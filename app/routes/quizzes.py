"""Quizzes — AI-generated MCQs by topic + count + difficulty."""
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from .. import db
from ..models import Quiz, QuizQuestion, StudyActivity
from ..forms import QuizForm
from ..services.ai_service import generate_quiz

quizzes_bp = Blueprint("quizzes", __name__)


@quizzes_bp.route("/")
@login_required
def index():
    items = (Quiz.query.filter_by(user_id=current_user.id)
             .order_by(Quiz.created_at.desc()).all())
    return render_template("quizzes/list.html", quizzes=items)


@quizzes_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = QuizForm()
    if request.method == "GET":
        pre = request.args.get("topic")
        if pre:
            form.topic.data = pre
    if form.validate_on_submit():
        topic = form.topic.data.strip()
        n = int(form.count.data)
        difficulty = form.difficulty.data
        quiz = Quiz(user_id=current_user.id,
                    title=f"{topic} ({difficulty})",
                    topic=topic, difficulty=difficulty)
        db.session.add(quiz)
        db.session.flush()
        for q in generate_quiz(topic, n=n, difficulty=difficulty):
            db.session.add(QuizQuestion(
                quiz_id=quiz.id, question=q["question"],
                options=json.dumps(q["options"]),
                correct_index=int(q["correct_index"]),
                explanation=q.get("explanation", ""),
            ))
        db.session.commit()
        flash(f"Generated {n} {difficulty} questions about '{topic}'.", "success")
        return redirect(url_for("quizzes.take", quiz_id=quiz.id))
    return render_template("quizzes/new.html", form=form)


@quizzes_bp.route("/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def take(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)
    parsed = [(q, json.loads(q.options)) for q in quiz.questions]
    if request.method == "POST":
        score = 0
        results = []
        for q, opts in parsed:
            chosen = request.form.get(f"q{q.id}")
            chosen_i = int(chosen) if chosen and chosen.isdigit() else -1
            correct = (chosen_i == q.correct_index)
            if correct:
                score += 1
            results.append({"q": q, "opts": opts,
                            "chosen": chosen_i, "correct": correct})
        quiz.score = score
        db.session.add(StudyActivity(user_id=current_user.id, kind="quiz"))
        db.session.commit()
        return render_template("quizzes/result.html", quiz=quiz,
                               results=results, total=len(parsed))
    return render_template("quizzes/take.html", quiz=quiz, parsed=parsed)


@quizzes_bp.route("/<int:quiz_id>/retake", methods=["POST"])
@login_required
def retake(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)
    quiz.score = None
    db.session.commit()
    return redirect(url_for("quizzes.take", quiz_id=quiz.id))


@quizzes_bp.route("/<int:quiz_id>/regenerate", methods=["POST"])
@login_required
def regenerate(quiz_id):
    """Generate a fresh quiz on the same topic/difficulty."""
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)
    QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
    n = int(request.form.get("count", 5))
    n = max(3, min(15, n))
    for q in generate_quiz(quiz.topic, n=n, difficulty=quiz.difficulty or "medium"):
        db.session.add(QuizQuestion(
            quiz_id=quiz.id, question=q["question"],
            options=json.dumps(q["options"]),
            correct_index=int(q["correct_index"]),
            explanation=q.get("explanation", ""),
        ))
    quiz.score = None
    db.session.commit()
    flash("New questions generated.", "success")
    return redirect(url_for("quizzes.take", quiz_id=quiz.id))


@quizzes_bp.route("/<int:quiz_id>/delete", methods=["POST"])
@login_required
def delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted.", "info")
    return redirect(url_for("quizzes.index"))