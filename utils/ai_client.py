import openai
import os
from dotenv import load_dotenv
import json

# Load API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_jd(inputs: dict) -> str:
    """Generate a professional JD using GPT-3.5-turbo."""
    prompt = f"""Generate a professional job description for:
Job Title: {inputs['title']}
Years of Experience: {inputs['experience']}
Must-have Skills: {inputs['skills']}
Company Name: {inputs['company']}
Employment Type: {inputs['type']}
Industry: {inputs['industry']}
Location: {inputs['location']}

Format with sections: Job Summary, Responsibilities, Requirements, Benefits.
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("OpenAI generate_jd error:", e)
        return ""


def match_resume_to_jd(jd_text: str, resume_text: str, filename: str) -> dict:
    """Compare resume to JD and return structured JSON."""
    prompt = f"""Compare this resume ({filename}) to the job description.

Job Description:
{jd_text}

Resume:
{resume_text}

Return ONLY valid JSON in this format:
{{
  "score": 0-100,
  "missing_skills": ["skill1","skill2"],
  "remarks": "short remark"
}}
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.0
        )
        content = resp["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print("match_resume_to_jd error:", e)
        return {"score": 0, "missing_skills": [], "remarks": "Matching failed"}


def generate_interview_email(candidate_name: str, job_title: str, remarks: str, jd_summary: str) -> str:
    """Generate interview invitation email."""
    prompt = f"""Write a professional interview invitation email for {candidate_name} for the role {job_title}.
Mention their strengths: {remarks}.
Include a short JD summary: {jd_summary[:300]}.
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("generate_interview_email error:", e)
        return "Could not generate interview email."


def generate_rejection_email(candidate_name: str, job_title: str, missing_skills: list) -> str:
    """Generate rejection email."""
    prompt = f"""Write a polite rejection email to {candidate_name} for the {job_title} role.
Mention missing skills: {', '.join(missing_skills)}.
Encourage them to apply again in the future.
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("generate_rejection_email error:", e)
        return "Could not generate rejection email."
