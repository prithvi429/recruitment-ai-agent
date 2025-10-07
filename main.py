from fastapi import FastAPI, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import shutil
from utils.text_extraction import extract_text_from_uploaded_file
from utils.ai_client import generate_jd, match_resume_to_jd, generate_interview_email, generate_rejection_email

app = FastAPI(title="Recruitment AI Agent", description="AI-powered resume matching")

templates = Jinja2Templates(directory="templates")
# No static files needed for this simple setup

# Global for session-like storage (in production, use sessions/DB)
current_jd = {"text": "", "summary": ""}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process_jd")
async def process_jd(
    request: Request,
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    experience: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    etype: Optional[str] = Form(None),  # 'type' is reserved
    industry: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    action: str = Form(...)
):
    global current_jd
    jd_content = ""
    
    if jd_file:
        contents = await jd_file.read()
        jd_content = extract_text_from_uploaded_file(contents, jd_file.filename)
    elif jd_text:
        jd_content = jd_text
    elif all([title, experience, skills, company, etype, industry, location]):
        inputs = {
            "title": title, "experience": experience, "skills": skills,
            "company": company, "type": etype, "industry": industry, "location": location
        }
        jd_content = generate_jd(inputs)
    else:
        return {"error": "Provide JD via file, text, or generation inputs."}
    
    if not jd_content:
        return {"error": "Failed to extract/generate JD."}
    
    current_jd["text"]