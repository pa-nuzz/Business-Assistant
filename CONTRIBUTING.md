# Contributing

Want to help out? Awesome. Here's what you need to know.

## Getting Started

You'll need:
- Python 3.12+
- Node.js 20+
- PostgreSQL 14+
- Redis 7+

### Quick Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/aeiou-ai.git
cd aeiou-ai

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate

# Frontend
cd frontend
npm install
npm run dev
```

### Running Locally

You'll need 3 terminals:

```bash
# Terminal 1 - Django
source .venv/bin/activate
python manage.py runserver

# Terminal 2 - Next.js (in frontend/ folder)
npm run dev

# Terminal 3 - Celery
source .venv/bin/activate
celery -A config worker -l info -B
```

## Code Layout

```
aeiou-ai/
├── api/           # API endpoints
├── config/        # Django config
├── core/          # Main business logic
├── frontend/      # Next.js app
└── utils/         # Shared utilities
```

## Workflow

### Branches

Name your branches like:
- `feature/task-filters`
- `fix/kanban-drag`
- `docs/readme-update`

### Commits

Keep it simple:
```
feat: add date filtering to tasks
fix: Kanban drag not working on mobile
docs: update setup instructions
```

### Pull Requests

1. Branch from `main`
2. Make your changes
3. Test it works
4. Open PR with a clear description

### Code Style

**Python:**
- PEP 8, type hints, docstrings for public functions

**TypeScript:**
- Strict mode, explicit types, interfaces for props

### Testing

```bash
# Backend
pytest

# Frontend
cd frontend && npm test

# E2E
npx playwright test
```

### Linting

```bash
# Python
flake8 core/
black core/ --check

# TypeScript
cd frontend && npm run lint
```

## Adding Stuff

### New API Endpoint

1. Add view in `api/v1/views/`
2. Add URL in `api/v1/urls.py`
3. Write tests
4. Update `API.md`

### New Model

1. Add to `core/models.py`
2. Run `python manage.py makemigrations`
3. Add to admin if needed
4. Write tests

### New Frontend Component

1. Add to `frontend/src/components/`
2. Add tests
3. Use it where needed

## Issues & Security

Found a bug? Open an issue with:
- What you did
- What you expected
- What actually happened
- Screenshots if it's a UI issue

**Security issues:** Email security@yourdomain.com privately. Don't post publicly until fixed.

## License

By contributing, you're agreeing to license your work under MIT.
