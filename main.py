from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import os

from utils.text_extraction import extract_text_from_uploaded_file
from utils.ai_client import (
    generate_jd,
    match_resume_to_jd,
    generate_interview_email,
    generate_rejection_email
)

app = FastAPI(
    title="Recruitment AI Agent",
    description="AI-powered resume matching and recruitment assistant"
)

templates = Jinja2Templates(directory="templates")

# Temporary in-memory storage (for prototype/demo)
current_jd = {"text": "", "summary": ""}
results = []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Show index page with JD input options"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_jd", response_class=HTMLResponse)
async def process_jd(
    request: Request,
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    experience: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    etype: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    action: str = Form(...)
):
    """Process JD via file upload, manual text, or AI generation"""
    global current_jd
    jd_content = ""

    # 1) Uploaded file
    if jd_file:
        contents = await jd_file.read()
        jd_content = extract_text_from_uploaded_file(contents, jd_file.filename)

    # 2) Manual JD text
    elif jd_text:
        jd_content = jd_text

    # 3) Generate JD using AI (if all fields provided)
    elif all([title, experience, skills, company, etype, industry, location]):
        inputs = {
            "title": title,
            "experience": experience,
            "skills": skills,
            "company": company,
            "type": etype,
            "industry": industry,
            "location": location
        }
        jd_content = generate_jd(inputs)

    if not jd_content:
        # render index with error message
        return templates.TemplateResponse("index.html", {"request": request, "error": "No JD provided or generation failed."})

    current_jd["text"] = jd_content
    current_jd["summary"] = jd_content[:400]

    return templates.TemplateResponse("index.html", {"request": request, "jd_text": jd_content})


@app.post("/upload_resumes", response_class=HTMLResponse)
async def upload_resumes(
    request: Request,
    resumes: List[UploadFile] = File(...)
):
    """Upload resumes, score them vs JD, show results"""
    global results
    results = []

    if not current_jd["text"]:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Please provide or generate a Job Description first."})

    # limit to 10 resumes for safety
    resumes = resumes[:10]

    for resume in resumes:
        contents = await resume.read()
        resume_text = extract_text_from_uploaded_file(contents, resume.filename)
        if not resume_text:
            match_result = {
                "filename": resume.filename,
                "score": 0,
                "missing_skills": ["Could not parse"],
                "remarks": "Failed to extract text from resume."
            }
        else:
            match_result = match_resume_to_jd(current_jd["text"], resume_text, resume.filename)
            match_result["filename"] = resume.filename

        results.append(match_result)

    # sort by score descending
    results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)

    return templates.TemplateResponse("results.html", {"request": request, "jd": current_jd, "results": results})


@app.get("/emails", response_class=HTMLResponse)
async def emails(request: Request):
    """Generate interview & rejection emails using AI"""
    if not results:
        return templates.TemplateResponse("index.html", {"request": request, "error": "No resumes processed yet."})

    best = results[0]
    interview_email = generate_interview_email(
        candidate_name=best.get("filename", "Candidate"),
        job_title=(current_jd["text"].splitlines()[0] if current_jd["text"] else "the role"),
        remarks=best.get("remarks", ""),
        jd_summary=current_jd.get("summary", "")
    )

    rejection_emails = []
    for c in results[1:]:
        rej = generate_rejection_email(
            candidate_name=c.get("filename", "Candidate"),
            job_title=(current_jd["text"].splitlines()[0] if current_jd["text"] else "the role"),
            missing_skills=c.get("missing_skills", [])
        )
        rejection_emails.append({"filename": c.get("filename"), "email": rej})

    return templates.TemplateResponse("results.html", {
        "request": request,
        "jd": current_jd,
        "results": results,
        "interview_email": interview_email,
        "rejection_emails": rejection_emails
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
