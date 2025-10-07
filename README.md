# Recruitment AI Agent

A small, practical web app for scoring resumes against a job description using AI assistance and lightweight resume parsing. Designed for local development and easy extension.

---

## Highlights

- Upload or paste a Job Description (JD) and upload candidate resumes (PDF / DOCX).
- Extracts text from resumes, scores and ranks candidates vs the JD using an AI model.
- Generates short emails (interview invites or polite rejections) based on results.
- Minimal, easy-to-read codebase: FastAPI backend, Jinja2 templates, and small utilities.

---

## Quick start (Windows PowerShell)

1. Create & activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Create a `.env` in the project root with your OpenAI key (optional, used if you enable AI features):

```
OPENAI_API_KEY=sk-...
```

4. Start the app (development mode)

```powershell
uvicorn main:app --reload
# or: python -m uvicorn main:app --reload
```

5. Open http://127.0.0.1:8000 in your browser.

Notes:
- If you prefer the bundled interpreter in `rec_env/`, run it explicitly: `rec_env\python.exe -m pip install -r requirements.txt` and start with `rec_env\python.exe -m uvicorn main:app --reload`.

---

## Endpoints / Pages

- `GET /` — Main page (`templates/index.html`) where you paste a JD and upload a resume.
- `POST /search` — Accepts the JD and uploaded resume, extracts text, scores the candidate(s), and returns rendered results (`templates/results.html`).

The app uses `utils/text_extraction.py` for PDF/DOCX parsing and `utils/ai_client.py` as the AI wrapper.

---

## Project layout

```
.
├── main.py                 # FastAPI app (routes + template wiring)
├── requirements.txt        # Python dependencies
├── templates/              # Jinja2 templates
│   ├── index.html
│   └── results.html
├── static/
│   └── styles.css          # App styles
└── utils/
    ├── text_extraction.py  # PDF/DOCX extractors (PyPDF2, python-docx)
    └── ai_client.py        # OpenAI wrapper + helpers
```

---

## How it works (internals)

1. The user posts a JD and an uploaded file.
2. `utils/text_extraction` extracts plain text from PDF or DOCX.
3. `utils/ai_client` calls the configured AI model to score and generate structured results (score, missing skills, remarks) and optional emails.
4. Results are rendered via `templates/results.html` that lists ranked candidates and provides mailto links.

Edge cases handled:
- Basic error handling for unreadable files.
- Defensive JSON parsing of AI outputs.

---

## Customization & Extensibility

- Swap the AI provider or model in `utils/ai_client.py` (there's a small wrapper to keep changes localized).
- Add OCR (Tesseract) for scanned PDFs by extending `utils/text_extraction.py`.
- Add persistent storage (SQLite/Postgres) to keep candidate records and history.

---

## Troubleshooting

- If templates don't render, ensure `jinja2` and `fastapi` are installed from `requirements.txt`.
- If PDF extraction returns empty text for scanned images, consider adding OCR (Tesseract + pytesseract).
- If OpenAI calls fail, verify `OPENAI_API_KEY` in `.env` or environment and confirm network access.

Run a quick import check to ensure modules load:

```powershell
python -c "import utils.text_extraction, utils.ai_client; print('imports OK')"
```

---

## Development notes

- Use the bundled `rec_env` interpreter only if you intentionally want the embedded interpreter shipped in this repo; otherwise create a fresh venv.
- Add unit tests for `utils/text_extraction` and `utils/ai_client` to lock behavior.

---

## License

This project includes a `LICENSE` file in the repository root.

---

If you'd like, I can now:

- Wire static styles into the templates (add `<link>` tags),
- Add example unit tests for the extractors, or
- Start the app in a terminal and verify the home page renders.

Tell me which next step you want and I'll implement it.
# recruitment-ai-agent
AI-powered Recruitment Assistant built with FastAPI — upload job descriptions &amp; resumes, get candidate scores, missing skills, and auto-generated interview/rejection emails.
