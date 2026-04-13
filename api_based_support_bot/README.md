# FYJC Support Bot (FastAPI + FAISS + Groq)

A dummy Maharashtra FYJC support website with a popup chatbot.

## Features
- FastAPI backend
- FAISS vector search over FAQ questions
- Multilingual embeddings (`intfloat/multilingual-e5-base` by default)
- Groq chat completion for bilingual responses (English + Marathi)
- Floating support popup bot on website

## Project structure
- `app/main.py` - FastAPI app and routes
- `app/bot.py` - Retrieval + Groq answer pipeline
- `templates/index.html` - Dummy gov-style website + popup bot UI
- `static/styles.css` - Styling
- `fyjc_faq_full.txt` - Full Q&A from site (questions + answers for better RAG).

## Setup
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Update `.env`:
   - `GROQ_API_KEY=...`
3. Run server:
   - `uvicorn app.main:app --reload`
4. Open:
   - `http://127.0.0.1:8000`

## Security & Production Notes
- CORS enabled (allow_origins=["*"] - tighten e.g. ["https://yourdomain.com"] for prod)
- Input validation max 500 chars
- Env-based config (keys/paths/models/k)
- Logging for errors (loguru)
- Prod: Add rate-limit (pip install slowapi), HTTPS, gunicorn/uvicorn workers

## Benchmarks (Local)
- Cold start: ~3s lighter model
- Query: <50ms retrieval
- RAG accuracy improved with Q&A context

## Notes
- Persistent FAISS auto-save/load
- Fallback no-key bilingual summary
- Q&A parsing robust
- Helpline integrated
- Tests: `pytest`
- Demo: http://127.0.0.1:8000
