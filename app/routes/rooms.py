"""Study Rooms – create/list collaborative study spaces."""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .. import db
from ..models import StudyRoom
from ..forms import RoomForm

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/")
@login_required
def index():
    rooms = (StudyRoom.query.filter_by(user_id=current_user.id)
             .order_by(StudyRoom.created_at.desc()).all())
    return render_template("rooms/list.html", rooms=rooms)


@rooms_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = RoomForm()
    if form.validate_on_submit():
        r = StudyRoom(user_id=current_user.id, name=form.name.data,
                      subject=form.subject.data, description=form.description.data)
        db.session.add(r)
        db.session.commit()
        flash("Study room created.", "success")
        return redirect(url_for("rooms.view", room_id=r.id))
    return render_template("rooms/new.html", form=form)


@rooms_bp.route("/<int:room_id>")
@login_required
def view(room_id):
    r = StudyRoom.query.get_or_404(room_id)
    if r.user_id != current_user.id:
        abort(403)
    return render_template("rooms/view.html", room=r)


@rooms_bp.route("/<int:room_id>/toggle", methods=["POST"])
@login_required
def toggle(room_id):
    r = StudyRoom.query.get_or_404(room_id)
    if r.user_id != current_user.id:
        abort(403)
    r.active = not r.active
    db.session.commit()
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:room_id>/delete", methods=["POST"])
@login_required
def delete(room_id):
    r = StudyRoom.query.get_or_404(room_id)
    if r.user_id != current_user.id:
        abort(403)
    db.session.delete(r)
    db.session.commit()
    flash("Room deleted.", "info")
    return redirect(url_for("rooms.index"))