"""Notes module – CRUD + AI summarisation."""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .. import db
from ..models import Note, StudyActivity
from ..forms import NoteForm
from ..services.ai_service import summarize

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/")
@login_required
def index():
    items = (Note.query.filter_by(user_id=current_user.id)
             .order_by(Note.updated_at.desc()).all())
    return render_template("notes/list.html", notes=items)


@notes_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.id, title=form.title.data,
                    content=form.content.data)
        db.session.add(note)
        db.session.add(StudyActivity(user_id=current_user.id, kind="note"))
        db.session.commit()
        flash("Note created.", "success")
        return redirect(url_for("notes.view", note_id=note.id))
    return render_template("notes/edit.html", form=form, mode="new")


@notes_bp.route("/<int:note_id>")
@login_required
def view(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    return render_template("notes/view.html", note=note)


@notes_bp.route("/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    form = NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        db.session.commit()
        flash("Note updated.", "success")
        return redirect(url_for("notes.view", note_id=note.id))
    return render_template("notes/edit.html", form=form, mode="edit")


@notes_bp.route("/<int:note_id>/summarize", methods=["POST"])
@login_required
def summarize_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    note.summary = summarize(note.content)
    db.session.commit()
    flash("AI summary generated.", "success")
    return redirect(url_for("notes.view", note_id=note.id))


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("notes.index"))