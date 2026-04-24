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

## Tech Stack

### Backend (Django 5)
| Component | Technology |
|-----------|------------|
| Framework | Django 5 + Django REST Framework |
| Database | PostgreSQL 15+ |
| Cache | Redis 7+ |
| Auth | JWT (djangorestframework-simplejwt) |
| AI | Gemini (primary), Groq (fallback), OpenRouter (backup) |
| Task Queue | Celery + Redis |
| Real-time | Django Channels + WebSocket |

### Frontend (Next.js 15)
| Component | Technology |
|-----------|------------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5.0 |
| Styling | TailwindCSS 4 |
| Components | shadcn/ui |
| State | React Context + Hooks |
| Charts | Recharts |
| Animations | Framer Motion |

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

## API Reference

### Authentication
```http
POST /api/v1/auth/register/    # Register new user
POST /api/v1/auth/login/       # Login (returns JWT + sets refresh cookie)
POST /api/v1/auth/logout/      # Logout (clears cookies)
POST /api/v1/auth/token/refresh/  # Refresh access token
```

### Chat
```http
POST /api/v1/chat/             # Send message (non-streaming)
POST /api/v1/chat/stream/      # Send message (SSE streaming)
WS /ws/chat/                   # WebSocket for real-time chat
```

### Tasks
```http
GET    /api/v1/tasks/              # List tasks
POST   /api/v1/tasks/create/       # Create task
GET    /api/v1/tasks/{id}/         # Get task details
PUT    /api/v1/tasks/{id}/update/  # Update task
DELETE /api/v1/tasks/{id}/delete/  # Delete task
POST   /api/v1/tasks/{id}/complete/
POST   /api/v1/tasks/{id}/reopen/
```

### Documents
```http
GET  /api/v1/documents/              # List documents
POST /api/v1/documents/upload/       # Upload document
GET  /api/v1/documents/{id}/status/  # Check processing status
```

### Analytics
```http
GET /api/v1/analytics/  # Dashboard analytics & insights
```

## Testing

```bash
# Backend tests
python manage.py test

# Specific modules
python manage.py test core.tests.test_chat_service
python manage.py test core.tests.test_task_service
python manage.py test core.tests.test_analytics_service

# With coverage
pytest --cov=core --cov=api --cov-report=html
```

## Deployment

### Render (Backend) + Vercel (Frontend)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy Backend to Render**
   - Connect GitHub repo
   - Use `render.yaml` (included)
   - Set environment variables in Render dashboard

3. **Deploy Frontend to Vercel**
   - Import GitHub repo
   - Set root directory to `frontend/`
   - Add `NEXT_PUBLIC_API_BASE_URL` environment variable

### Docker (Optional)

```bash
# Coming soon - Docker support in development
```

## Project Structure

```
aeiou-ai/
├── api/                    # REST API endpoints
│   ├── views/              # Modular view files
│   ├── auth_views.py       # Authentication
│   ├── task_views.py       # Task management
│   └── views/analytics_views.py  # Analytics
├── core/                   # Core business logic
│   ├── models.py           # Database models
│   ├── services/           # Service layer pattern
│   │   ├── chat_service.py
│   │   ├── task_service.py
│   │   ├── analytics_service.py
│   │   └── ...
│   ├── events/             # Event bus
│   ├── cache.py            # Redis utilities
│   └── tests/              # Unit tests
├── agents/                 # AI orchestration
│   ├── orchestrator.py     # Main AI orchestrator
│   ├── entity_resolver.py  # Entity resolution
│   └── tool_decision.py    # Tool selection
├── services/               # External integrations
│   ├── model_layer.py      # AI model abstraction
│   ├── document.py         # Document processing
│   └── email_service.py    # Email sending
├── frontend/               # Next.js application
│   ├── app/                # App router pages
│   ├── components/         # React components
│   ├── hooks/              # Custom hooks
│   └── lib/                # Utilities & API
└── config/                 # Django configuration
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Workflow

1. **Create Service** in `core/services/`
2. **Add View** in `api/views/`
3. **Write Tests** in `core/tests/`
4. **Update Cache** keys if needed
5. **Emit Events** for side effects

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- 📧 Email: support@aeiou.ai
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/aeiou-ai/issues)
- 📖 Docs: [Full Documentation](https://docs.aeiou.ai)

---

<div align="center">

Built with ❤️ using Next.js, Django, and AI

</div>
