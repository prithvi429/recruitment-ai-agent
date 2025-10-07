from __future__ import annotations

import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from utils.text_extraction import extract_text_from_uploaded_file, AllowedExtensionError
from utils.ai_client import (
    generate_jd_summary,
    match_resume_to_jd,
    generate_interview_email,
    generate_rejection_email,
)

APP_TITLE = "Recruitment AI Agent"
APP_DESC = "AI-powered resume matching and recruitment assistant (rewritten, safe fallbacks)"
MAX_FILE_SIZE_MB = 10
ALLOWED_UPLOADS = {".pdf", ".docx", ".txt"}

app = FastAPI(title=APP_TITLE, description=APP_DESC)

# Mount /static for CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def _init_state() -> None:
    if not hasattr(app.state, "jd"):
        app.state.jd: Dict[str, Any] = {"text": "", "summary": ""}
    if not hasattr(app.state, "results"):
        app.state.results: List[Dict[str, Any]] = []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the index page."""
    _init_state()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jd": app.state.jd,
            "results": app.state.results,
            "error": None,
        },
    )


@app.post("/jd/summary", response_class=HTMLResponse)
async def jd_summary(request: Request, jd_text: str = Form(...)):
    """Generate JD summary using AI or fallback."""
    _init_state()
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")
    try:
        summary = generate_jd_summary(jd_text.strip())
        app.state.jd = {"text": jd_text.strip(), "summary": summary}
        app.state.results = []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize JD: {e}")
    return templates.TemplateResponse(
        "results.html",
        {"request": request, "jd": app.state.jd, "results": app.state.results, "email": None},
    )


@app.post("/resumes/upload", response_class=HTMLResponse)
async def upload_resumes(request: Request, files: List[UploadFile] = File(...)):
    """Upload resumes and score them."""
    _init_state()
    if not app.state.jd.get("text"):
        raise HTTPException(status_code=400, detail="Please provide a JD first.")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results: List[Dict[str, Any]] = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_UPLOADS:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")
        if file.size and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{file.filename} is too large.")

        try:
            text = await extract_text_from_uploaded_file(file)
        except AllowedExtensionError as e:
            raise HTTPException(status_code=415, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to read {file.filename}: {e}")

        try:
            score, details = match_resume_to_jd(text, app.state.jd["text"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to score {file.filename}: {e}")

        results.append(
            {
                "filename": file.filename,
                "score": round(float(score) * 100, 2),
                "details": details,
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    app.state.results = results

    return templates.TemplateResponse(
        "results.html",
        {"request": request, "jd": app.state.jd, "results": app.state.results, "email": None},
    )


@app.post("/email/generate", response_class=HTMLResponse)
async def email_generate(
    request: Request,
    email_type: str = Form(...),
    candidate_name: str = Form(...),
    candidate_email: Optional[str] = Form(None),
):
    """Generate interview or rejection email."""
    _init_state()
    if email_type not in {"interview", "rejection"}:
        raise HTTPException(status_code=400, detail="Invalid email_type.")
    if not candidate_name.strip():
        raise HTTPException(status_code=400, detail="candidate_name is required.")

    if email_type == "interview":
        email = generate_interview_email(candidate_name.strip(), app.state.jd.get("text", ""))
    else:
        email = generate_rejection_email(candidate_name.strip())

    return templates.TemplateResponse(
        "results.html",
        {"request": request, "jd": app.state.jd, "results": app.state.results, "email": email, "candidate_email": candidate_email},
    )
