import PyPDF2
from docx import Document
from typing import Optional

def extract_text_from_file(file_path: str) -> Optional[str]:
    """Extract text from PDF or DOCX file."""
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return text.strip()
    elif file_path.endswith(('.doc', '.docx')):
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text.strip()
    return None

def extract_text_from_uploaded_file(contents: bytes, filename: str) -> Optional[str]:
    """Extract text from uploaded file bytes (for FastAPI)."""
    # Save temp file (in production, use BytesIO)
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return extract_text_from_file(tmp_path)
    finally:
        import os
        os.unlink(tmp_path)