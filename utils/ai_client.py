from __future__ import annotations
import os, re
from typing import Tuple, Dict, Any
from math import isfinite
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # fallback

_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def _openai_client():
    if _OPENAI_KEY and OpenAI:
        return OpenAI(api_key=_OPENAI_KEY)
    return None


def _basic_sentences(text: str, max_sentences: int = 3) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts[:max_sentences]) if parts else text.strip()


def generate_jd_summary(jd_text: str) -> str:
    client = _openai_client()
    if client:
        try:
            prompt = f"Summarize this JD in 4–6 bullet points:\n\n{jd_text}"
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass
    return _basic_sentences(jd_text, 5)


def match_resume_to_jd(resume_text: str, jd_text: str) -> Tuple[float, Dict[str, Any]]:
    docs = [resume_text or "", jd_text or ""]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vectorizer.fit_transform(docs)
    sim = cosine_similarity(X[0:1], X[1:2])[0][0]
    if not isfinite(sim):
        sim = 0.0

    resume_tokens = set(re.findall(r"[A-Za-z0-9_+#.-]+", resume_text.lower()))
    jd_tokens = set(re.findall(r"[A-Za-z0-9_+#.-]+", jd_text.lower()))
    overlap = sorted(list(resume_tokens & jd_tokens))[:30]

    details = {"method": "tfidf_cosine", "top_overlap_terms": overlap}
    return float(sim), details


def generate_interview_email(candidate_name: str, jd_text: str) -> str:
    client = _openai_client()
    if client:
        try:
            prompt = f"Write a short interview invitation email for {candidate_name}.\n\nJD:\n{jd_text}"
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass
    return f"""Subject: Interview Invitation

Hi {candidate_name},

Thank you for applying. We’d love to schedule a 30–45 minute conversation about the role. 
Please share your availability.

Best regards,
Recruitment Team
"""


def generate_rejection_email(candidate_name: str) -> str:
    client = _openai_client()
    if client:
        try:
            prompt = f"Write a short rejection email for {candidate_name}."
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass
    return f"""Subject: Application Update

Hi {candidate_name},

Thank you for your time and application. After review, we won’t be moving forward. 
We encourage you to apply for future opportunities.

Best regards,
Recruitment Team
"""
