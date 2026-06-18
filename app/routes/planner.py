"""AI Study Planner — multiple plans, grouped by day, with progress."""
from collections import OrderedDict
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   abort, request)
from flask_login import login_required, current_user
from .. import db
from ..models import StudyPlan, PlanItem
from ..forms import PlannerForm
from ..services.ai_service import generate_plan

planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/")
@login_required
def index():
    plans = (StudyPlan.query.filter_by(user_id=current_user.id)
             .order_by(StudyPlan.created_at.desc()).all())
    return render_template("planner/list.html", plans=plans)


@planner_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = PlannerForm()
    if request.method == "GET":
        pre = request.args.get("goal")
        if pre:
            form.goal.data = pre
    if form.validate_on_submit():
        goal = form.goal.data.strip()
        days = int(form.days.data)
        plan = StudyPlan(user_id=current_user.id, goal=goal, days=days)
        db.session.add(plan)
        db.session.flush()

        items = generate_plan(goal, days)
        for it in items:
            db.session.add(PlanItem(
                plan_id=plan.id,
                day=it.get("day", "Day 1"),
                topic=it.get("topic", "Topic"),
                detail=it.get("detail", ""),
            ))
        db.session.commit()
        flash(f"Generated a {days}-day plan for '{goal}'.", "success")
        return redirect(url_for("planner.view", plan_id=plan.id))
    return render_template("planner/new.html", form=form)


@planner_bp.route("/<int:plan_id>")
@login_required
def view(plan_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)
    groups = OrderedDict()
    for it in plan.items:
        groups.setdefault(it.day, []).append(it)
    return render_template("planner/view.html", plan=plan, groups=groups)


@planner_bp.route("/<int:plan_id>/toggle/<int:item_id>", methods=["POST"])
@login_required
def toggle(plan_id, item_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)
    it = PlanItem.query.get_or_404(item_id)
    if it.plan_id != plan.id:
        abort(403)
    it.done = not it.done
    db.session.commit()
    return redirect(url_for("planner.view", plan_id=plan.id))


@planner_bp.route("/<int:plan_id>/regenerate", methods=["POST"])
@login_required
def regenerate(plan_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)
    PlanItem.query.filter_by(plan_id=plan.id).delete()
    items = generate_plan(plan.goal, plan.days)
    for it in items:
        db.session.add(PlanItem(
            plan_id=plan.id,
            day=it.get("day", "Day 1"),
            topic=it.get("topic", "Topic"),
            detail=it.get("detail", ""),
        ))
    db.session.commit()
    flash("Plan regenerated.", "success")
    return redirect(url_for("planner.view", plan_id=plan.id))


@planner_bp.route("/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete(plan_id):
    plan = StudyPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)
    db.session.delete(plan)
    db.session.commit()
    flash("Plan deleted.", "info")
    return redirect(url_for("planner.index"))