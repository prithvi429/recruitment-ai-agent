from __future__ import annotations
import os, tempfile
from typing import Optional
from fastapi import UploadFile
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

class AllowedExtensionError(Exception):
    pass

ALLOWED_EXTS = {".pdf", ".docx", ".txt"}


async def extract_text_from_uploaded_file(file: UploadFile) -> str:
    name = file.filename or "uploaded"
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise AllowedExtensionError(f"Unsupported extension: {ext}")

    suffix = ext if ext in {".pdf", ".docx"} else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if ext == ".pdf":
            text = pdf_extract_text(tmp_path) or ""
        elif ext == ".docx":
            doc = Document(tmp_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        return text.strip()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
