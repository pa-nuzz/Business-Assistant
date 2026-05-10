# What's New

This is where I track what I've been building and fixing.

## Version 1.0.0 - January 2025

This is the first proper release. Took way longer than I expected, but here we are.

### What I Built

**The Basics (Foundation)**
- Django backend with PostgreSQL. Tried SQLite first, quickly learned my lesson.
- Next.js frontend. Started with plain React, Next.js was worth the switch.
- JWT auth that actually works. Refresh tokens, the whole deal.
- User accounts with email/password.
- Basic task management - create, edit, delete, the usual stuff.

**AI Features**
- Hooked up multiple AI providers (Gemini, Groq, OpenRouter) so I'm not dependent on one.
- Chat interface where you can actually talk to the AI about your work.
- Auto task generation from conversations. This is genuinely useful - saves me typing.
- Document upload and processing. Drag PDFs in, get summaries out.
- Semantic search so you can find stuff by meaning, not just keywords.

**Document Stuff**
- PDF and text file support. DOCX coming later maybe.
- Chat with your documents. Ask questions, get answers.
- Auto summarization for long docs.
- Entity extraction (finds names, dates, companies, etc).
- Similarity search - "find me docs like this one."

**Background Processing**
- Celery for async tasks. Documents take time to process.
- Real job status tracking. No more wondering if something's stuck.
- WebSocket updates so the UI knows when stuff finishes.

**Team Features**
- Kanban board with drag-and-drop. Had to fight React DnD for this one.
- Comments on tasks with @mentions.
- Subtasks - break big things into smaller pieces.
- Time tracking. Simple but works.
- Activity feed so you know what's happening.

**Workspaces & Access**
- Multi-workspace support. Separate spaces for different teams/projects.
- Roles: Owner, Admin, Member, Viewer. Keeps things organized.
- Invite by email. Simple but effective.
- Permission controls on resources.

**Integrations**
- REST API with proper versioning.
- API tokens for connecting other tools.
- Webhooks with HMAC signing for security.
- Zapier/Make.com endpoints if you're into that.

**Performance**
- Redis caching. Made a huge difference.
- Query optimization. Django Debug Toolbar was my friend here.
- Rate limiting so people don't abuse the API.

**Mobile**
- PWA support. Works like a native app on phones.
- Mobile-optimized Kanban. Touch-friendly drag and drop.
- Works offline for basic stuff.

**Analytics**
- Tracking what features people actually use.
- AI usage and cost tracking. Those API bills add up.
- Basic retention metrics.
- GDPR-compliant data export/delete.

### Tech Stack

- **Backend:** Django 5, Django REST Framework, Celery, PostgreSQL
- **Frontend:** Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui
- **AI:** Gemini, Groq, OpenRouter
- **Other:** Redis, Nginx

### API

Currently at v1. Stable enough to build on.

### Breaking Changes

None yet - this is the first release.

### Security Stuff

- JWT authentication
- Rate limiting
- Signed webhooks
- XSS/CSRF protection
- Argon2 password hashing

### Performance Notes

- Redis caching with compression
- Database queries are optimized
- Background processing for heavy tasks
- Lazy loading for big lists

### Known Issues

None major. Small bugs get fixed as they come up.

---

*Last updated: January 2025*
