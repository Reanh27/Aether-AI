"""PDF text extraction.

1. Try fast text extraction with pypdf (text-based PDFs).
2. If empty, fall back to OCR.space HTTP API (works on Render!).
"""
import io
import requests
from pypdf import PdfReader
from flask import current_app


MAX_CHARS = 50_000
OCR_ENDPOINT = "https://api.ocr.space/parse/image"


def _extract_with_pypdf(data, max_chars=MAX_CHARS):
    """Return (text, pages, error)."""
    reader = PdfReader(io.BytesIO(data))
    pages = len(reader.pages)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            return "", pages, "This PDF is password-protected."
    chunks = []
    total = 0
    for page in reader.pages:
        try:
            txt = (page.extract_text() or "").strip()
        except Exception:
            txt = ""
        if txt:
            chunks.append(txt)
            total += len(txt)
            if total > max_chars:
                break
    return "\n\n".join(chunks).strip(), pages, None


def _extract_with_ocr(data, filename="document.pdf"):
    """Return (text, error). Uses OCR.space HTTP API."""
    api_key = current_app.config.get("OCR_API_KEY", "")
    language = current_app.config.get("OCR_LANGUAGE", "eng")
    if not api_key:
        return "", ("This looks like a scanned PDF. "
                    "OCR isn't configured — ask the admin to set OCR_API_KEY.")
    try:
        files = {"file": (filename, data, "application/pdf")}
        body = {
            "apikey": api_key,
            "language": language,
            "isOverlayRequired": "false",
            "filetype": "PDF",
            "OCREngine": "2",   # better engine for scans
            "scale": "true",
            "isTable": "false",
        }
        resp = requests.post(OCR_ENDPOINT, data=body, files=files, timeout=90)
        if resp.status_code >= 300:
            return "", f"OCR service returned HTTP {resp.status_code}."
        data_json = resp.json()
        if data_json.get("IsErroredOnProcessing"):
            err = data_json.get("ErrorMessage", ["Unknown OCR error"])
            err_msg = err[0] if isinstance(err, list) else str(err)
            return "", f"OCR error: {err_msg}"
        results = data_json.get("ParsedResults") or []
        text = "\n\n".join((r.get("ParsedText") or "").strip()
                           for r in results).strip()
        if not text:
            return "", "OCR ran but didn't find any readable text."
        return text[:MAX_CHARS], None
    except requests.Timeout:
        return "", "OCR took too long — try a smaller PDF (under 5 MB)."
    except Exception as e:
        return "", f"OCR failed: {e}"


def extract_text(file_storage):
    """Main entry. Returns (text, pages, ocr_used, error)."""
    try:
        data = file_storage.read()
        if not data:
            return "", 0, False, "The file is empty."
        size_mb = len(data) / (1024 * 1024)

        # Step 1: try pypdf
        text, pages, err = _extract_with_pypdf(data)
        if err:
            return "", pages, False, err
        if text:
            return text[:MAX_CHARS], pages, False, None

        # Step 2: OCR fallback for scanned PDFs
        if size_mb > 5:
            return "", pages, False, (
                "This PDF appears to be scanned and is too large for OCR "
                f"({size_mb:.1f} MB). Please use a PDF under 5 MB.")
        filename = getattr(file_storage, "filename", "document.pdf") or "document.pdf"
        ocr_text, ocr_err = _extract_with_ocr(data, filename=filename)
        if ocr_err:
            return "", pages, True, ocr_err
        return ocr_text, pages, True, None
    except Exception as e:
        return "", 0, False, f"Could not read the PDF: {e}"