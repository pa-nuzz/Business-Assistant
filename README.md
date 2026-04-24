# AEIOU AI — Business Assistant

An AI-powered business assistant that helps small-to-medium business owners manage operations through natural conversation. Combines document intelligence, task management, and business analytics in one unified interface.

## What It Does

| Feature | Capability |
|---------|------------|
| **AI Chat** | Conversational AI with business context awareness and persistent memory |
| **Task Management** | Full-featured system with subtasks, assignments, comments, time tracking, and AI-suggested actions |
| **Document Processing** | Secure upload of PDFs, DOCX, TXT with magic bytes validation |
| **Business Profile** | Store company information, goals, key metrics, and analytics |
| **Real-time Streaming** | Live chat responses via Server-Sent Events (SSE) |
| **Security** | Rate limiting, SSRF protection, JWT authentication, input sanitization |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 + React 18 + TypeScript)              │
│  ├── Tailwind CSS + shadcn/ui components                    │
│  ├── Framer Motion animations                               │
│  └── JWT authentication with auto-refresh                   │
├─────────────────────────────────────────────────────────────┤
│  Backend (Django 5.0 + DRF)                                 │
│  ├── JWT Authentication (simplejwt)                         │
│  ├── Rate limiting & throttling                             │
│  └── Input sanitization & validation                        │
├─────────────────────────────────────────────────────────────┤
│  MCP Layer (Model Context Protocol)                         │
│  ├── Orchestrator (intent classification, planning)         │
│  ├── Tool Registry (15+ business tools)                     │
│  └── Memory Store (structured, no vector DB)                │
├─────────────────────────────────────────────────────────────┤
│  AI Providers                                               │
│  ├── Gemini (primary)                                       │
│  ├── Groq (fast fallback)                                   │
│  └── OpenRouter (backup)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (optional, for production only)

### Step 1: Backend Setup

```bash
# Navigate and setup
cd "/Users/danuzz/Documents/Mero Projects/AEIOU AI"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: Add API keys, generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(50))"

# Initialize database
python manage.py migrate
python manage.py createsuperuser  # optional

# Start server
python manage.py runserver
```

**Backend:** http://127.0.0.1:8000

### Step 2: Frontend Setup

```bash
cd "/Users/danuzz/Documents/Mero Projects/AEIOU AI/frontend"
npm install
npm run dev
```

**Frontend:** http://localhost:3000

### Step 3: Verify

| Service | URL | Test |
|---------|-----|------|
| Backend Health | http://127.0.0.1:8000/api/v1/health/ | Should return `{"status": "ok"}` |
| Django Admin | http://127.0.0.1:8000/admin/ | Login page |
| Frontend App | http://localhost:3000 | Your Next.js app |

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required
```env
# Django
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_hex(50))"
DEBUG=False  # Set to True for development only
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (uses SQLite by default, configure PostgreSQL for production)
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### AI Providers (at least one required)
```env
# Gemini (Primary - recommended, free tier: 1M tokens/day)
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash-latest

# Groq (Fast fallback, free tier available)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama3-8b-8192

# OpenRouter (Final fallback, has free models)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

### Email Configuration
```env
# For development (prints emails to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# For production (Gmail SMTP example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Your App <your-email@gmail.com>
```

### Production Security
```env
# Enable HTTPS
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Create new account with email verification |
| POST | `/api/v1/auth/login/` | Login and get JWT tokens |
| POST | `/api/v1/auth/verify-email/` | Verify email with 6-digit code |
| POST | `/api/v1/auth/forgot-password/` | Request password reset code |
| POST | `/api/v1/auth/reset-password/` | Reset password with verification code |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/` | Send message and get AI response |
| POST | `/api/v1/chat/stream/` | Streaming AI response (SSE) |
| GET | `/api/v1/conversations/` | List user's conversations |
| GET | `/api/v1/conversations/{id}/` | Get conversation details |
| DELETE | `/api/v1/conversations/{id}/delete/` | Delete conversation |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/` | List tasks with filtering and pagination |
| POST | `/api/v1/tasks/create/` | Create new task |
| GET | `/api/v1/tasks/{id}/` | Get task details |
| PUT | `/api/v1/tasks/{id}/update/` | Update task |
| DELETE | `/api/v1/tasks/{id}/delete/` | Delete (archive) task |
| POST | `/api/v1/tasks/{id}/complete/` | Mark task as complete |
| POST | `/api/v1/tasks/{id}/reopen/` | Reopen completed task |
| GET | `/api/v1/tasks/dashboard/` | Get task dashboard data |
| GET | `/api/v1/tasks/stats/` | Get task statistics |

### Task Comments & Activity
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/{id}/comments/` | List task comments |
| POST | `/api/v1/tasks/{id}/comments/` | Add comment to task |
| DELETE | `/api/v1/tasks/{id}/comments/{cid}/` | Delete comment |
| GET | `/api/v1/tasks/{id}/activities/` | List task activity history |

### Task Suggestions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/suggestions/` | List AI-suggested tasks |
| POST | `/api/v1/tasks/suggestions/{id}/accept/` | Accept suggestion and create task |
| POST | `/api/v1/tasks/suggestions/{id}/reject/` | Reject suggestion |

### Tags
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tags/` | List all tags |
| POST | `/api/v1/tags/` | Create new tag |
| GET | `/api/v1/tags/{name}/tasks/` | Get tasks by tag |
| POST | `/api/v1/tasks/{id}/tags/` | Add tag to task |
| DELETE | `/api/v1/tasks/{id}/tags/` | Remove tag from task |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload/` | Upload document (PDF, DOCX, TXT) |
| GET | `/api/v1/documents/` | List uploaded documents |
| GET | `/api/v1/documents/{id}/summary/` | Get document summary |
| DELETE | `/api/v1/documents/{id}/delete/` | Delete document |

### User Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/PUT | `/api/v1/profile/` | Get/update business profile |
| GET | `/api/v1/user/info/` | Get current user info |
| POST | `/api/v1/user/update-password/` | Update password |

## Security Best Practices

### 1. Secret Management
- **Never commit `.env` files** to version control
- Use strong, randomly generated `SECRET_KEY` in production
- Rotate API keys regularly
- Use different keys for development and production
- **After pulling this repo, generate new API keys immediately** — old keys in git history are compromised

### 2. Rate Limiting (New)
All endpoints are protected with throttling:
```
auth_register:     5/hour    (prevents spam registration)
auth_verify:       10/min    (prevents brute force on codes)
auth_password:     5/hour    (prevents password reset abuse)
auth_login:        10/min    (prevents brute force login)
chat:              20/min    (prevents API abuse)
upload:            10/min    (prevents upload spam)
task:              60/min    (read operations)
task_write:        30/min    (create/update/delete)
conversation:      100/min   (conversation listing)
```

### 3. HTTPS in Production
```env
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 4. File Upload Security (Enhanced)
- **Magic bytes validation** — actual file content checked (not just extension)
- Blocked signatures: Windows executables (MZ), ELF, PHP scripts, shell scripts
- PDF: Must start with `%PDF`
- DOCX: Valid ZIP with `word/document.xml` inside
- TXT: Readable text only, no script patterns
- Size limits enforced (configurable, default 10MB)
- Path traversal protection in filenames
- Files stored outside web root

### 5. Authentication (Enhanced)
- JWT tokens with short lifetime (30 minutes access, 3 days refresh)
- Automatic token rotation
- Blacklist old tokens
- Email verification required before login
- **Cryptographically secure verification codes** (secrets.randbelow, not random.randint)
- Code attempt limiting (max 5 attempts before lockout)
- Automatic cleanup of expired/used reset codes

### 6. SSRF Protection (New)
Web scraping tool validates URLs before fetching:
- Blocks internal IPs (10.x, 172.x, 192.168.x, 127.x)
- Blocks localhost and loopback
- Blocks cloud metadata endpoints (169.254.169.254)
- Blocks internal TLDs (.internal, .local, .corp)
- Only allows http/https schemes

### 7. Input Validation
- All user inputs sanitized using bleach
- SQL injection protection via Django ORM
- XSS protection with proper escaping
- CSRF protection enabled
- UUID validation for document IDs
- Tool argument sanitization (user_id enforced from session)

## Deployment

### Using Render (Recommended)
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with included `render.yaml`

### Manual Deployment
1. Set `DEBUG=False`
2. Configure production database
3. Run `python manage.py collectstatic`
4. Set up HTTPS
5. Configure email backend
6. Set up Redis for caching/Celery

## Development

### Running Tests
```bash
# Django tests
python manage.py test

# With coverage
coverage run manage.py test
coverage report
```

### Code Style
- Follow PEP 8 for Python
- Use ESLint/Prettier for JavaScript/TypeScript
- Type hints recommended for Python functions

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Migration errors** | `python manage.py makemigrations && python manage.py migrate` |
| **Rate limit (429)** | Wait and retry. Auth: 5-10/hr, Chat: 20/min, Uploads: 10/min |
| **File upload rejected** | Check magic bytes: PDF=`%PDF`, DOCX=valid ZIP with `word/document.xml` |
| **AI timeouts** | Verify API keys in `.env`, check provider status pages |
| **Import errors** | `pip install -r requirements.txt` |
| **Email in dev** | Check terminal output — emails print to console by default |

## License

MIT License — see LICENSE file

## Support

1. Check troubleshooting above
2. Review `.env` configuration
3. Verify API keys at provider dashboards
4. Check logs: `python manage.py runserver` output
5. Run tests: `python manage.py test`

**Security fixes documented in:** `SECURITY_FIXES.md`
