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
# Serve with uvicorn (not runserver): it streams SSE live and serves the
# channels WebSockets, and binds IPv4+IPv6 so http://localhost:8000 works in
# Chrome, Firefox, and Safari (Firefox resolves `localhost` to ::1).
python -m uvicorn config.asgi:application --host :: --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000. The Next.js app proxies all `/api/v1/*`
requests to the backend same-origin (see `frontend/src/app/api/v1/[...path]/route.ts`),
so the browser only ever talks to `localhost:3000`.

### Email deliverability (why automated mail goes to spam)

Transactional email (verification codes, password resets, login alerts) is built
in `services/email_service.py`. Every message already carries a `Reply-To`
(so replies reach a monitored inbox) and a unique `Message-ID`. What decides
deliverability is DNS + the `From` header:

1. **Align `DEFAULT_FROM_EMAIL` with the SMTP account you actually send from.**
   When `EMAIL_HOST=smtp.gmail.com`, the envelope sender is your Gmail account,
   so `From:` must be that same address (a custom display name is fine, e.g.
   `AEIOU AI <sent-from@gmail.com>`). Sending `From: noreply@aeiou.ai` through
   Gmail fails SPF/DKIM alignment because the domain isn't the one Gmail signed.
2. **SPF** — publish the Google TXT record for `yourdomain.com`:
   `v=spf1 include:_spf.google.com ~all`
3. **DKIM** — Gmail: Settings → Accounts → "Sign in with Google" → Enable DKIM
   for the sending Gmail account (auto-signs all mail). For ESMTP/Postfix or
   SendGrid/Mailgun, generate a DKIM key and publish it as a TXT record.
4. **DMARC** — publish so receivers know how to treat spoofed mail:
   `v=DMARC1; p=none; rua=mailto:postmaster@yourdomain.com` while monitoring,
   then tighten `p=quarantine` once legitimate mail passes.
5. **Watch bounces/spam-feedback** — Gmail suppressions appear in Google Admin;
   keep complaint rate < 0.1%. Warm up a new sender address before volume.

Verification of deliverability: send a test login alert with the SMTP backend
and check the raw headers for `Authentication-Results: spf=pass`, `dkim=pass`,
`dmarc=pass`, plus `Reply-To` and `Message-ID`.

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

