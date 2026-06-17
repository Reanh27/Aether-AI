"""PDF text extraction helper.

Reads uploaded PDF bytes and returns the plain-text content.
Skips images / scanned pages (no OCR).
"""
import io
from pypdf import PdfReader


MAX_CHARS = 50_000  # cap extracted text so the AI prompt stays small


def extract_text(file_storage):
    """
    Given a Flask FileStorage, return (text, page_count, error).
    `error` is None on success, otherwise a friendly message.
    """
    try:
        data = file_storage.read()
        if not data:
            return "", 0, "The file is empty."
        reader = PdfReader(io.BytesIO(data))
        pages = len(reader.pages)
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # try empty password
            except Exception:
                return "", pages, "This PDF is password-protected."
        chunks = []
        total_chars = 0
        for page in reader.pages:
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            txt = txt.strip()
            if txt:
                chunks.append(txt)
                total_chars += len(txt)
                if total_chars > MAX_CHARS:
                    break
        text = "\n\n".join(chunks).strip()
        if not text:
            return "", pages, ("No selectable text found. "
                               "If your PDF is a scanned image, OCR isn't supported yet.")
        return text[:MAX_CHARS], pages, None
    except Exception as e:
        return "", 0, f"Could not read the PDF: {e}"