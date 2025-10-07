from __future__ import annotations
import os, re, math
from typing import Tuple, Dict, Any
from collections import Counter

# Try to import new OpenAI client (v1.x)
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Config
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_OPENAI_KEY = os.getenv("OPENAI_API_KEY")


# ----------------------------
# Utility functions
# ----------------------------
def _openai_client():
    """Return OpenAI client if API key is available, else None."""
    if _OPENAI_KEY and OpenAI:
        return OpenAI(api_key=_OPENAI_KEY)
    return None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_+#.-]+", (text or "").lower())


def _cosine_on_counts(a: Counter, b: Counter) -> float:
    """Compute cosine similarity between two Counters of tokens."""
    keys = set(a.keys()) | set(b.keys())
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1e-9
    nb = math.sqrt(sum(v * v for v in b.values())) or 1e-9
    return float(dot / (na * nb))


# ----------------------------
# JD Summary
# ----------------------------
def generate_jd_summary(jd_text: str) -> str:
    """Generate a concise JD summary using OpenAI if available, else fallback."""
    client = _openai_client()
    if client:
        try:
            prompt = (
                "Summarize this job description in 4–6 bullet points covering: "
                "role, must-have skills, nice-to-haves, experience level, location/remote, and responsibilities.\n\n"
                f"JD:\n{jd_text}"
            )
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] OpenAI summary failed, using fallback. Error: {e}")

    # ---- Fallback: first 5 sentences ----
    parts = re.split(r"(?<=[.!?])\s+", (jd_text or "").strip())
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts[:5]) or jd_text.strip()


# ----------------------------
# Resume Matching
# ----------------------------
def match_resume_to_jd(resume_text: str, jd_text: str) -> Tuple[float, Dict[str, Any]]:
    """Return (similarity_score_0_to_1, details) comparing resume vs JD."""
    rt = _tokenize(resume_text)
    jt = _tokenize(jd_text)

    rc = Counter(rt)
    jc = Counter(jt)

    score = _cosine_on_counts(rc, jc)

    # Extract top overlap words
    overlap = (rc & jc)
    top_overlap = [w for w, _ in overlap.most_common(30)]

    details = {
        "method": "cosine_similarity_local",
        "top_overlap_terms": top_overlap,
    }
    return score, details


# ----------------------------
# Email Generation
# ----------------------------
def generate_interview_email(candidate_name: str, jd_text: str) -> str:
    """Generate an interview invite email."""
    client = _openai_client()
    if client:
        try:
            prompt = (
                f"Write a concise, friendly interview invite email to {candidate_name}. "
                "Propose a 30–45 min call, ask for availability + timezone. "
                "Infer the role title if possible from the JD.\n\n"
                f"JD:\n{jd_text}"
            )
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] OpenAI interview email failed, using fallback. Error: {e}")

    # ---- Fallback ----
    return (
        f"Subject: Interview Invitation\n\n"
        f"Hi {candidate_name},\n\n"
        "Thank you for your application. We’d love to schedule a 30–45 minute conversation to discuss the role. "
        "Please share your availability (with timezone) over the next few days.\n\n"
        "Best regards,\nRecruitment Team"
    )


def generate_rejection_email(candidate_name: str) -> str:
    """Generate a polite rejection email."""
    client = _openai_client()
    if client:
        try:
            prompt = (
                f"Write a brief and empathetic rejection email to {candidate_name}. "
                "Thank them for applying and encourage future applications. Keep it under 150 words."
            )
            resp = client.chat.completions.create(
                model=_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] OpenAI rejection email failed, using fallback. Error: {e}")

    # ---- Fallback ----
    return (
        f"Subject: Application Update\n\n"
        f"Hi {candidate_name},\n\n"
        "Thank you for your time and application. After review, we won’t be moving forward. "
        "We encourage you to apply for future opportunities.\n\n"
        "Best regards,\nRecruitment Team"
    )
