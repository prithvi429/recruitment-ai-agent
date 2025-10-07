import openai
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_jd(inputs: dict) -> str:
    """Generate a professional Job Description using GPT-3.5."""
    prompt = f"""
    Generate a professional job description for:
    - Job Title: {inputs['title']}
    - Years of Experience: {inputs['experience']}
    - Must-have Skills: {inputs['skills']}
    - Company Name: {inputs['company']}
    - Employment Type: {inputs['type']}
    - Industry: {inputs['industry']}
    - Location: {inputs['location']}

    Format the output into:
    1. Job Summary
    2. Key Responsibilities
    3. Required Skills & Qualifications
    4. Benefits
    """
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Error in generate_jd:", e)
        return ""


def match_resume_to_jd(jd_text: str, resume_text: str, filename: str) -> dict:
    """Score resume vs JD and return structured JSON."""
    prompt = f"""
    Compare this resume to the job description and give a structured JSON response.

    Job Description:
    {jd_text}

    Resume ({filename}):
    {resume_text}

    Return ONLY valid JSON with this format:
    {{
        "score": 0-100,
        "missing_skills": ["skill1", "skill2"],
        "remarks": "short feedback"
    }}
    """
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.0
        )
        content = resp["choices"][0]["message"]["content"].strip()
        # Remove code block markers if present
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print("Error in match_resume_to_jd:", e)
        return {"score": 0, "missing_skills": [], "remarks": "Failed to parse AI response"}


def generate_interview_email(candidate_name: str, job_title: str, remarks: str, jd_summary: str) -> str:
    """Generate a personalized interview email."""
    prompt = f"""
    Write a professional interview invitation email for {candidate_name} 
    applying for the role {job_title}.
    Highlight their strengths: {remarks}.
    Include a short JD summary: {jd_summary[:250]}.
    
    Structure:
    - Subject
    - Greeting
    - Body
    - Call to Action
    - Sign-off
    """
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.3
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Error in generate_interview_email:", e)
        return "Could not generate interview email."


def generate_rejection_email(candidate_name: str, job_title: str, missing_skills: list) -> str:
    """Generate a polite rejection email."""
    prompt = f"""
    Write a polite rejection email to {candidate_name} 
    for the role {job_title}.
    Mention missing skills: {', '.join(missing_skills)}.
    Encourage them to apply in the future.
    
    Structure:
    - Subject
    - Greeting
    - Body
    - Closing
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
        print("Error in generate_rejection_email:", e)
        return "Could not generate rejection email."
