# AEIOU AI

A business assistant that actually gets work done. Chat with AI to manage tasks, upload documents for insights, and track your business goals — all in one place.

**Stack:** Next.js 15 + Django 5 + PostgreSQL + Redis

## Features

- **AI Chat** — Talk naturally about your business, get actionable answers
- **Task Management** — Full task system with AI suggestions, comments, time tracking
- **Documents** — Upload PDFs/DOCX/TXT, get summaries and answers
- **Business Profile** — Store company info, goals, and metrics
- **Real-time Updates** — WebSocket support for live notifications
- **Performance Optimized** — Redis caching, response compression, query optimization

## Architecture

### Backend (Django)
- **Service Layer Pattern** — Business logic extracted from views into reusable services
- **Event-Driven** — Event bus for decoupled component communication
- **Caching** — Redis for frequently accessed data
- **Rate Limiting** — Scoped rate limiting per endpoint
- **Security** — JWT authentication, input sanitization, audit logging

### Frontend (Next.js 15)
- **React 19** — Latest React with concurrent features
- **TypeScript** — Type-safe development
- **TailwindCSS** — Utility-first styling
- **shadcn/ui** — Modern component library

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
5. Set up Redis for caching (optional but recommended)

See `.env.example` for all options.

## Testing

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test core.tests.test_auth_service
python manage.py test core.tests.test_task_service
python manage.py test core.tests.test_integration

# Run with coverage
pip install pytest pytest-django pytest-cov
pytest --cov=core --cov=api
```

## Deployment

See `DEPLOY.md` for detailed deployment instructions (Render/Vercel).

Quick version:
1. Set `DEBUG=False` in production
2. Configure PostgreSQL database
3. Set up Redis for caching
4. Set up SMTP email (Gmail works fine)
5. Deploy backend to Render, frontend to Vercel

## API Overview

All endpoints under `/api/v1/`. Key routes:
- `POST /auth/login/` — Returns JWT access token + sets refresh cookie
- `POST /chat/` — Send message to AI
- `GET/POST /tasks/` — Task management
- `POST /documents/upload/` — Upload PDF/DOCX/TXT
- `GET/POST /profile/` — Business profile management

### Authentication
All endpoints require JWT authentication except:
- `POST /auth/register/`
- `POST /auth/login/`
- `POST /auth/verify-email/`
- `POST /auth/forgot-password/`

### Rate Limits
- Auth endpoints: 20/min
- Standard endpoints: 60/min
- Write operations: 10/min
- File uploads: 5/min

## Security

- JWT with httpOnly refresh cookies
- Rate limiting on all endpoints
- File uploads validated by magic bytes
- Input sanitized with bleach
- Audit logging for sensitive actions
- CORS configured for frontend domain
- Security headers (CSP, XSS protection)

## Project Structure

```
AEIOU AI/
├── api/                    # API views and routing
│   ├── views/             # Modular view files
│   ├── auth_views.py      # Authentication endpoints
│   └── task_views.py      # Task management endpoints
├── core/                   # Core application
│   ├── models.py          # Database models
│   ├── services/         # Business logic layer
│   ├── events/            # Event bus implementation
│   ├── cache.py           # Redis caching utilities
│   └── tests/             # Unit and integration tests
├── config/                 # Django configuration
│   └── settings/          # Environment-specific settings
├── services/               # External service integrations
│   ├── document.py        # Document processing
│   ├── email_service.py   # Email sending
│   └── model_layer.py     # AI model interactions
├── utils/                  # Utility functions
│   ├── middleware/        # Custom middleware
│   └── sanitization.py    # Input sanitization
└── frontend/              # Next.js frontend
```

## Development

### Adding New Features

1. **Create Service** — Add business logic to `core/services/`
2. **Create View** — Add API endpoint in `api/views/`
3. **Add Tests** — Write unit tests in `core/tests/`
4. **Update Cache** — Add cache invalidation if needed
5. **Publish Events** — Emit events for side effects

### Code Style

- Python: PEP 8, use black for formatting
- TypeScript: ESLint + Prettier
- Commit messages: Conventional Commits

MIT License
