# AEIOU AI

A business assistant that actually helps. Chat, manage tasks, work with documents, and keep track of what matters—all in one place.

Built with Next.js 15, Django 5, TypeScript, and Python 3.12.

## What It Does

**Chat with AI that understands your work**
- Have actual conversations, not just Q&A
- Upload documents and ask questions about them
- AI suggests tasks from your conversations
- It remembers your context—no repeating yourself

**Task management that doesn't suck**
- Kanban board with real drag-and-drop
- Due dates, priorities, assignments
- Time tracking built in
- Comments and @mentions for team coordination

**Fast and responsive**
- Live AI responses (you can see it typing)
- Instant notifications for updates
- Command palette for keyboard shortcuts (Cmd+K)

**Actually secure**
- JWT auth with proper token handling
- Rate limiting to prevent abuse
- Input sanitization
- Audit logs for important actions

## Getting Started

You'll need:
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Setup

```bash
# Clone
git clone https://github.com/yourusername/aeiou-ai.git
cd aeiou-ai

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000

### Configuration

Copy `.env.example` to `.env` and set:

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/aeiou
REDIS_URL=redis://localhost:6379/0

# At least one AI API key
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key
```

See `.env.example` for all options.

