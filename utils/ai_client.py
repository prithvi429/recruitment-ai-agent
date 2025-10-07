import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not set!")

client = openai.OpenAI(api_key=openai.api_key)

def generate_jd(inputs: dict) -> str:
    """Generate JD using GPT."""
    prompt = f"""Generate a professional job description for:
- Job Title: {inputs['title']}
- Years of Experience: {inputs['experience']}
- Must-have Skills: {inputs['skills']}
- Company Name: {inputs['company']}
- Employment Type: {inputs['type']}
- Industry: {inputs['industry']}
- Location: {inputs['location']}

Output in a structured, readable format (e.g., sections for Responsibilities, Requirements)."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def match_resume_to_jd(jd_text: str, resume_text: str, filename: str) -> dict:
    """Match resume to JD and get score, missing skills, remarks."""
    prompt = f"""Compare this resume ({filename}): {resume_text}
To this Job Description: {jd_text}

Analyze relevance. Output ONLY valid JSON:
{{
    "score": <integer 0-100>,
    "missing_skills": ["skill1", "skill2"],
    "remarks": "<brief explanation, e.g., Strong in Python but lacks AWS experience>"
}}"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    try:
        # Parse JSON from response
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()  # Remove markdown
        return json.loads(content)
    except json.JSONDecodeError:
        return {"score": 0, "missing_skills": ["Error parsing"], "remarks": "Matching failed"}

def generate_interview_email(candidate_name: str, job_title: str, remarks: str, jd_summary: str) -> str:
    """Generate personalized interview call email."""
    prompt = f"""Generate a professional, personalized email inviting {candidate_name} for an interview for the {job_title} role.
Highlight their strengths: {remarks}.
Include a summary of the JD: {jd_summary[:200]}...
Subject: Invitation to Interview - {job_title} at [Company]
Structure: Greeting, Body, Call to Action, Sign-off."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def generate_rejection_email(candidate_name: str, job_title: str, missing_skills: list) -> str:
    """Generate polite rejection email."""
    prompt = f"""Generate a polite rejection email for {candidate_name} who applied for {job_title}.
Mention missing skills: {', '.join(missing_skills)}.
Encourage future applications.
Subject: Update on Your Application - {job_title}
Structure: Greeting, Body, Closing."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()