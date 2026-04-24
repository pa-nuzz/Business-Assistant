<div align="center">

# AEIOU AI

**Your AI Business Partner** — Chat, manage tasks, analyze documents, and track goals in one intelligent workspace.

[![Stack](https://img.shields.io/badge/Stack-Next.js%2015%20%2B%20Django%205-6366f1)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776ab)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6)](https://typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-10b981)](LICENSE)

</div>

## Features

### AI-Powered Business Assistant
- **Intelligent Chat** — Natural conversations with context-aware responses
- **Document Intelligence** — Upload PDFs, DOCX, TXT for AI analysis and summaries
- **Task Automation** — AI suggests tasks from conversations, auto-extracts action items
- **Business Context** — Remembers your company, goals, and metrics

### Full-Featured Task Management
- **Kanban Board** — Visual task organization with drag-and-drop
- **Smart Scheduling** — Due dates, priorities, assignments
- **Time Tracking** — Log hours, track productivity
- **Comments & Collaboration** — Team discussions on tasks

### Real-Time Experience
- **WebSocket Streaming** — Live AI responses with typing indicators
- **Instant Notifications** — Task updates, mentions, due date reminders
- **Command Palette** — Keyboard shortcuts for power users (Cmd+K)

### Enterprise-Grade Security
- **JWT Authentication** — Access tokens in memory, refresh in httpOnly cookies
- **Rate Limiting** — Per-endpoint throttling prevents abuse
- **Input Sanitization** — All user input sanitized with bleach
- **Audit Logging** — Track sensitive actions for compliance

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/aeiou-ai.git
cd aeiou-ai
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Edit .env with your database and API keys

# Database setup
python manage.py migrate
python manage.py createsuperuser  # Optional

# Run server
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000/api/v1/
- **Admin**: http://127.0.0.1:8000/admin/

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/aeiou
REDIS_URL=redis://localhost:6379/0

# AI APIs (at least one required)
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

