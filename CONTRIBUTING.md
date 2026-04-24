# Contributing to AEIOU AI

Thank you for your interest in contributing to AEIOU AI! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/aeiou-ai.git
   cd aeiou-ai
   ```

2. **Setup Backend**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your settings
   python manage.py migrate
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints where possible
- Run `black` for formatting
- Run `flake8` for linting
- Write docstrings for all public functions

### TypeScript (Frontend)
- Use strict TypeScript
- Follow ESLint rules
- Use Prettier for formatting
- Prefer functional components with hooks

## Making Changes

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Development Workflow

For backend features:
1. Create service in `core/services/`
2. Add view in `api/views/`
3. Write tests in `core/tests/`
4. Update cache keys if needed
5. Add URL route in `api/v1/urls.py`

For frontend features:
1. Create components in `frontend/src/components/`
2. Add pages in `frontend/src/app/`
3. Update API layer in `frontend/src/lib/api.ts`
4. Follow design system (slate/indigo colors)

### 3. Testing

```bash
# Backend tests
python manage.py test

# Specific module
python manage.py test core.tests.test_chat_service

# Coverage
pytest --cov=core --cov=api
```

### 4. Commit Messages

Use conventional commits format:
```
feat: add new analytics endpoint
fix: resolve chat streaming error
docs: update README
refactor: simplify task service
test: add tests for auth service
```

## Pull Request Process

1. **Before Submitting**
   - Ensure all tests pass
   - Update documentation if needed
   - Add screenshots for UI changes
   - Rebase on latest main branch

2. **PR Description**
   - Describe what changed and why
   - Reference any related issues
   - List breaking changes if any
   - Include testing instructions

3. **Review Process**
   - Address review comments
   - Keep discussion constructive
   - Update PR as needed

## Project Structure

```
aeiou-ai/
├── api/              # Django REST API
├── core/             # Core business logic & models
├── agents/           # AI orchestration layer
├── services/         # External integrations
├── frontend/         # Next.js application
└── config/           # Django configuration
```

## Reporting Issues

When reporting bugs, include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Node versions)
- Screenshots if applicable
- Error messages/logs

## Security Issues

Please report security vulnerabilities to security@aeiou.ai privately.
Do not open public issues for security problems.

## Questions?

- Open a GitHub Discussion
- Email: dev@aeiou.ai

Thank you for contributing! 🎉
