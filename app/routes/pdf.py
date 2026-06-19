"""PDF / Document summary tool — upload PDF or paste text."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from .. import db
from ..models import Note
from ..forms import PdfSummaryForm, PdfUploadForm
from ..services.ai_service import summarize
from ..services.pdf_extract import extract_text

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Upload a PDF file → extract text (with OCR fallback) → AI summary."""
    form = PdfUploadForm()
    summary = None
    saved_title = None
    ocr_used = False

    if form.validate_on_submit():
        file = form.pdf.data
        original_name = (file.filename or "document.pdf").rsplit(".", 1)[0]
        title = (form.title.data or "").strip() or original_name

        text, pages, ocr_used, err = extract_text(file)
        if err:
            flash(err, "danger")
            return redirect(url_for("pdf.index"))

        summary = summarize(text)
        saved_title = f"[PDF] {title}"
        note = Note(user_id=current_user.id,
                    title=saved_title, content=text, summary=summary)
        db.session.add(note)
        db.session.commit()
        ocr_msg = " (extracted via OCR)" if ocr_used else ""
        flash(f"Summarized {pages} page(s){ocr_msg}. Saved to your Notes.",
              "success")

    return render_template("pdf/index.html", form=form,
                           summary=summary, saved_title=saved_title,
                           ocr_used=ocr_used)


@pdf_bp.route("/paste", methods=["GET", "POST"])
@login_required
def paste():
    """Paste text directly (no PDF needed)."""
    form = PdfSummaryForm()
    summary = None
    saved_title = None
    if form.validate_on_submit():
        summary = summarize(form.content.data)
        saved_title = f"[Doc] {form.title.data}"
        note = Note(user_id=current_user.id,
                    title=saved_title, content=form.content.data,
                    summary=summary)
        db.session.add(note)
        db.session.commit()
        flash("Summary generated and saved to your Notes.", "success")
    return render_template("pdf/paste.html", form=form,
                           summary=summary, saved_title=saved_title)


@pdf_bp.route("/download")
@login_required
def download():
    """Download text passed via query param as .txt."""
    text = request.args.get("text", "")
    filename = request.args.get("name", "summary") + ".txt"
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )