# AEIOU AI

A business assistant that actually gets work done. Chat with AI to manage tasks, upload documents for insights, and track your business goals — all in one place.

**Stack:** Next.js 15 + Django + PostgreSQL

## Features

- **AI Chat** — Talk naturally about your business, get actionable answers
- **Task Management** — Full task system with AI suggestions, comments, time tracking
- **Documents** — Upload PDFs/DOCX/TXT, get summaries and answers
- **Business Profile** — Store company info, goals, and metrics

## Quick Start

```bash
# Backend
cd "AEIOU AI"
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python manage.py migrate
python manage.py runserver

# Frontend (new terminal)
cd "AEIOU AI/frontend"
npm install
npm run dev
```

Backend runs at http://127.0.0.1:8000, frontend at http://localhost:3000.

## Setup

1. Copy `.env.example` to `.env`
2. Generate a secret key: `python -c "import secrets; print(secrets.token_hex(50))"`
3. Add at least one AI API key (Gemini recommended — free tier is generous)
4. Set up PostgreSQL database (local or cloud)

See `.env.example` for all options.

## Deployment

See `DEPLOY.md` for detailed deployment instructions (Render/Vercel).

Quick version:
1. Set `DEBUG=False` in production
2. Configure PostgreSQL database
3. Set up SMTP email (Gmail works fine)
4. Deploy backend to Render, frontend to Vercel

## API Overview

All endpoints under `/api/v1/`. Key routes:
- `POST /auth/login/` — Returns JWT access token + sets refresh cookie
- `POST /chat/` — Send message to AI
- `GET/POST /tasks/` — Task management
- `POST /documents/upload/` — Upload PDF/DOCX/TXT

Full API docs in code or check `docs/ROUTES.md`.

## Security

- JWT with httpOnly refresh cookies
- Rate limiting on all endpoints
- File uploads validated by magic bytes
- Input sanitized with bleach
- Audit logging for sensitive actions

## Dev Notes

Tests: `python manage.py test`
Lint: `npm run lint` (frontend), `flake8` (backend)

MIT License
