"""Study Rooms — create, share via invite code, join, chat with members."""
import secrets
import string
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   abort, request)
from flask_login import login_required, current_user
from .. import db
from ..models import StudyRoom, RoomMember, RoomMessage
from ..forms import RoomForm, JoinRoomForm, RoomMessageForm

rooms_bp = Blueprint("rooms", __name__)


def _gen_invite_code(length=6):
    """Generate a unique 6-char alphanumeric invite code."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c in code for c in "01OI"):  # skip ambiguous chars
            continue
        if not StudyRoom.query.filter_by(invite_code=code).first():
            return code
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _user_can_view(room, user_id):
    if room.user_id == user_id:
        return True
    return RoomMember.query.filter_by(room_id=room.id, user_id=user_id).first() is not None


@rooms_bp.route("/")
@login_required
def index():
    owned = (StudyRoom.query.filter_by(user_id=current_user.id)
             .order_by(StudyRoom.created_at.desc()).all())
    joined_ids = [m.room_id for m in
                  RoomMember.query.filter_by(user_id=current_user.id).all()]
    joined = (StudyRoom.query
              .filter(StudyRoom.id.in_(joined_ids),
                      StudyRoom.user_id != current_user.id)
              .order_by(StudyRoom.created_at.desc()).all()) if joined_ids else []
    join_form = JoinRoomForm()
    return render_template("rooms/list.html",
                           owned=owned, joined=joined, join_form=join_form)


@rooms_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = RoomForm()
    if form.validate_on_submit():
        r = StudyRoom(user_id=current_user.id,
                      name=form.name.data,
                      subject=form.subject.data,
                      description=form.description.data,
                      invite_code=_gen_invite_code())
        db.session.add(r)
        db.session.commit()
        flash(f"Room created! Share code: {r.invite_code}", "success")
        return redirect(url_for("rooms.view", room_id=r.id))
    return render_template("rooms/new.html", form=form)


@rooms_bp.route("/join", methods=["POST"])
@login_required
def join():
    form = JoinRoomForm()
    if not form.validate_on_submit():
        flash("Please enter a valid invite code.", "danger")
        return redirect(url_for("rooms.index"))
    code = form.code.data.strip().upper()
    room = StudyRoom.query.filter_by(invite_code=code).first()
    if not room:
        flash(f"No room found with code '{code}'.", "danger")
        return redirect(url_for("rooms.index"))
    if room.user_id == current_user.id:
        flash("You own this room — no need to join.", "info")
        return redirect(url_for("rooms.view", room_id=room.id))
    existing = RoomMember.query.filter_by(
        room_id=room.id, user_id=current_user.id).first()
    if not existing:
        db.session.add(RoomMember(room_id=room.id, user_id=current_user.id))
        db.session.commit()
        flash(f"Joined '{room.name}'!", "success")
    else:
        flash("You're already a member.", "info")
    return redirect(url_for("rooms.view", room_id=room.id))


@rooms_bp.route("/<int:room_id>", methods=["GET", "POST"])
@login_required
def view(room_id):
    room = StudyRoom.query.get_or_404(room_id)
    if not _user_can_view(room, current_user.id):
        abort(403)
    msg_form = RoomMessageForm()
    if msg_form.validate_on_submit():
        db.session.add(RoomMessage(room_id=room.id,
                                   user_id=current_user.id,
                                   content=msg_form.content.data))
        db.session.commit()
        return redirect(url_for("rooms.view", room_id=room.id))
    is_owner = (room.user_id == current_user.id)
    return render_template("rooms/view.html", room=room,
                           is_owner=is_owner, msg_form=msg_form)


@rooms_bp.route("/<int:room_id>/leave", methods=["POST"])
@login_required
def leave(room_id):
    room = StudyRoom.query.get_or_404(room_id)
    if room.user_id == current_user.id:
        flash("Owners can't leave — delete the room instead.", "warning")
        return redirect(url_for("rooms.view", room_id=room.id))
    m = RoomMember.query.filter_by(
        room_id=room.id, user_id=current_user.id).first()
    if m:
        db.session.delete(m)
        db.session.commit()
        flash(f"Left '{room.name}'.", "info")
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:room_id>/kick/<int:member_id>", methods=["POST"])
@login_required
def kick(room_id, member_id):
    room = StudyRoom.query.get_or_404(room_id)
    if room.user_id != current_user.id:
        abort(403)
    m = RoomMember.query.get_or_404(member_id)
    if m.room_id != room.id:
        abort(403)
    db.session.delete(m)
    db.session.commit()
    flash("Member removed.", "info")
    return redirect(url_for("rooms.view", room_id=room.id))


@rooms_bp.route("/<int:room_id>/toggle", methods=["POST"])
@login_required
def toggle(room_id):
    room = StudyRoom.query.get_or_404(room_id)
    if room.user_id != current_user.id:
        abort(403)
    room.active = not room.active
    db.session.commit()
    return redirect(url_for("rooms.view", room_id=room.id))


@rooms_bp.route("/<int:room_id>/new-code", methods=["POST"])
@login_required
def new_code(room_id):
    room = StudyRoom.query.get_or_404(room_id)
    if room.user_id != current_user.id:
        abort(403)
    room.invite_code = _gen_invite_code()
    db.session.commit()
    flash(f"New invite code: {room.invite_code}", "success")
    return redirect(url_for("rooms.view", room_id=room.id))


@rooms_bp.route("/<int:room_id>/delete", methods=["POST"])
@login_required
def delete(room_id):
    room = StudyRoom.query.get_or_404(room_id)
    if room.user_id != current_user.id:
        abort(403)
    db.session.delete(room)
    db.session.commit()
    flash("Room deleted.", "info")
    return redirect(url_for("rooms.index"))