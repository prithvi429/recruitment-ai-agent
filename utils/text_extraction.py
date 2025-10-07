import PyPDF2
from docx import Document
from typing import Optional
import os

# Optional OCR dependencies are used if installed
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_ENABLED = True
except Exception:
    OCR_ENABLED = False


def extract_text_from_pdf_file(path: str) -> str:
    text = ""
    try:
        reader = PyPDF2.PdfReader(path)
        for page in reader.pages:
            ptext = page.extract_text()
            if ptext:
                text += ptext + "\n"
    except Exception as e:
        print("PyPDF2 error:", e)

    if not text.strip() and OCR_ENABLED:
        try:
            images = convert_from_path(path)
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            print("OCR error:", e)

    return text.strip()


def extract_text_from_docx_file(path: str) -> str:
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        print("DOCX read error:", e)
        return ""


def extract_text_from_file(path: str) -> Optional[str]:
    path = path.lower()
    if path.endswith(".pdf"):
        return extract_text_from_pdf_file(path)
    if path.endswith((".docx", ".doc")):
        return extract_text_from_docx_file(path)
    return None


def extract_text_from_uploaded_file(contents: bytes, filename: str) -> Optional[str]:
    """For FastAPI: write bytes to a temp file and extract text."""
    import tempfile
    suffix = filename if filename.startswith(".") else os.path.splitext(filename)[1] or ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(contents)
        tmp.flush()
        tmp.close()
        text = extract_text_from_file(tmp.name)
        return text
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
