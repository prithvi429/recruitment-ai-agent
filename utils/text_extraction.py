from __future__ import annotations
import os, tempfile
from fastapi import UploadFile

# Try PDF extractors
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except Exception:
    pdf_extract_text = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

from docx import Document  # pip install python-docx


class AllowedExtensionError(Exception):
    """Raised if uploaded file has unsupported extension."""


ALLOWED_EXTS = {".pdf", ".docx", ".txt"}


async def extract_text_from_uploaded_file(file: UploadFile) -> str:
    """
    Extract text from uploaded file (PDF/DOCX/TXT).
    Uses pdfminer.six or PyPDF2 for PDF.
    """
    name = file.filename or "uploaded"
    ext = os.path.splitext(name)[1].lower()

    if ext not in ALLOWED_EXTS:
        raise AllowedExtensionError(
            f"Unsupported extension: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTS))}"
        )

    suffix = ext if ext in {".pdf", ".docx"} else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = ""
        if ext == ".pdf":
            if pdf_extract_text is not None:
                try:
                    text = pdf_extract_text(tmp_path) or ""
                except Exception as e:
                    print(f"[WARN] pdfminer failed, falling back to PyPDF2: {e}")
            if (not text) and PyPDF2 is not None:
                try:
                    with open(tmp_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        pages = [p.extract_text() or "" for p in reader.pages]
                    text = "\n".join(pages)
                except Exception as e:
                    print(f"[ERROR] PyPDF2 failed too: {e}")
            if not text:
                raise RuntimeError("No PDF extractor available. Install pdfminer.six or PyPDF2.")
        
        elif ext == ".docx":
            try:
                doc = Document(tmp_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception as e:
                raise RuntimeError(f"Failed to read DOCX: {e}")
        
        else:  # .txt
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        return text.strip()

    finally:
        try:
            os.unlink(tmp_path)  # cleanup temp file
        except Exception:
            pass
