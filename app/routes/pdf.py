"""PDF / Document summary tool (paste text, get an AI summary)."""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Note
from ..forms import PdfSummaryForm
from ..services.ai_service import summarize

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = PdfSummaryForm()
    summary = None
    if form.validate_on_submit():
        summary = summarize(form.content.data)
        note = Note(user_id=current_user.id,
                    title=f"[PDF] {form.title.data}",
                    content=form.content.data, summary=summary)
        db.session.add(note)
        db.session.commit()
        flash("Summary saved to your Notes.", "success")
    return render_template("pdf/index.html", form=form, summary=summary)