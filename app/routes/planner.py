"""AI Study Planner – generates a multi-day learning schedule."""
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from .. import db
from ..models import PlanItem
from ..forms import PlannerForm
from ..services.ai_service import generate_plan

planner_bp = Blueprint("planner", __name__)

@planner_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = PlannerForm()
    if request.method == "GET":
        pre = request.args.get("goal")
        if pre:
            form.goal.data = pre
    items = (PlanItem.query.filter_by(user_id=current_user.id)
             .order_by(PlanItem.id.asc()).all())
    if form.validate_on_submit():
        plan = generate_plan(form.goal.data, int(form.days.data))
        for it in plan:
            db.session.add(PlanItem(
                user_id=current_user.id,
                day=it.get("day", "Day 1"),
                topic=it.get("topic", "Topic"),
                detail=it.get("detail", ""),
            ))
        db.session.commit()
        flash(f"Generated a {form.days.data}-day plan for '{form.goal.data}'.", "success")
        return redirect(url_for("planner.index"))
    return render_template("planner/index.html", form=form, items=items)


@planner_bp.route("/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle(item_id):
    it = PlanItem.query.get_or_404(item_id)
    if it.user_id != current_user.id:
        abort(403)
    it.done = not it.done
    db.session.commit()
    return redirect(url_for("planner.index"))


@planner_bp.route("/clear", methods=["POST"])
@login_required
def clear():
    PlanItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Plan cleared.", "info")
    return redirect(url_for("planner.index"))