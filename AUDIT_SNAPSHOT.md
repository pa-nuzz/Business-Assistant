# AEIOU AI - Codebase Audit Snapshot
**Generated**: Pre-overhaul v1 (pre-overhaul-v1 tag)
**Branch**: feat/overhaul-v2
**Audit Date**: 2026-04-24

---

## 📊 File Counts by Type

| Type | Count |
|------|-------|
| Python (.py) | 53 |
| TypeScript (.ts/.tsx) | 61 |
| CSS (.css) | 26 |
| **Total Source Files** | **140** |

---

## 🐍 Django Backend Structure

### Django Apps
- **api** - REST API views, routing, consumers (7 files)
- **core** - Models, admin, migrations, tests (5 files)
- **agents** - AI orchestration, entity resolver, prompts (6 files)
- **config** - Settings (base, dev, prod), URLs, ASGI, Celery (10 files)
- **services** - Document processing, email, Gemini, Groq, OpenRouter, model layer (7 files)
- **utils** - Logger, middleware, sanitization (6 files)
- **mcp** - MCP servers, tools (5 files)

### Key Backend Files
| File | Lines | Notes |
|------|-------|-------|
| `api/views.py` | 1172 | **God file - needs splitting** |
| `api/task_views.py` | ~600 | Already split out |
| `api/auth_views.py` | ~400 | Auth endpoints |
| `agents/orchestrator.py` | ~600 | AI orchestration |
| `core/models.py` | ~500 | All models |
| `services/document.py` | ~300 | Document processing |

---

## ⚛️ Next.js Frontend Structure

### App Router Pages
- `/` - Landing
- `/login` - Authentication
- `/register` - Registration
- `/forgot-password` - Password reset request
- `/reset-password` - Password reset confirm
- `/verify-email` - Email verification
- `/dashboard` - Main dashboard
- `/chat` - Chat interface
- `/documents` - Document management
- `/tasks` - Task management
- `/settings` - User settings

### Components (16 files)
- `ui/` - shadcn/ui components
- `sidebar-new.tsx` - Navigation
- `enhanced-command-palette.tsx` - Command palette
- `onboarding-wizard.tsx` - User onboarding
- `notification-bell.tsx`, `floating-notification-widget.tsx` - Notifications
- Various UI components

### Key Frontend Files
| File | Purpose |
|------|---------|
| `src/lib/api.ts` | API client (15 localStorage refs - needs httpOnly refactor) |
| `src/hooks/use-cross-tab-sync.ts` | Cross-tab state sync |

---

## 🔍 Code Quality Issues Found

### Print Statements
```
api/views.py: Uses logger properly
services/document.py: Clean
```
**Status**: Good - already using logging

### Bare Except Blocks
- `api/views.py:79` - `except Exception: pass` (business_profile lookup)
- `api/views.py:171` - `except Exception: pass` (business_profile lookup in chat_stream)
- Multiple in business_profile view for avatar deletion

### TODO Comments
```
No active TODO comments found in project code
```

### localStorage Usage (15 refs in `src/lib/api.ts`)
**Critical for Phase 1.3**: JWT tokens stored in localStorage need migration to httpOnly cookies

---

## 🗂️ API Endpoints Inventory

### Authentication
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/password-reset/`
- `POST /api/auth/password-reset-confirm/`
- `POST /api/auth/email-verify/`
- `POST /api/auth/resend-verification/`

### Chat
- `POST /api/chat/` - Send message
- `POST /api/chat/stream/` - Streaming response
- `GET /api/conversations/` - List conversations (paginated)
- `GET /api/conversations/{id}/` - Get conversation
- `DELETE /api/conversations/{id}/` - Delete conversation
- `GET /api/conversations/{id}/export/` - Export conversation

### Documents
- `GET /api/documents/` - List documents (paginated)
- `POST /api/documents/upload/` - Upload document
- `GET /api/documents/{id}/status/` - Check processing status
- `DELETE /api/documents/{id}/` - Delete document
- `GET /api/documents/{id}/summary/` - Get AI summary

### User & Profile
- `GET /api/user/` - Get current user info
- `POST /api/user/username/` - Update username
- `POST /api/user/password/` - Update password
- `GET /api/business-profile/` - Get profile
- `POST /api/business-profile/` - Update profile
- `GET /api/business-analytics/` - Dashboard stats

### Tasks (in task_views.py)
- Full CRUD endpoints
- Kanban state updates
- Task suggestions from AI

### Onboarding
- `GET /api/onboarding/status/` - Check progress
- `POST /api/onboarding/complete/` - Mark complete
- `POST /api/onboarding/seed-demo/` - Seed demo data

---

## ⚠️ Critical Issues for Phase 1

### 1. God View File
**File**: `api/views.py` (1172 lines)
**Issue**: Contains auth, chat, documents, profile, onboarding, tasks logic
**Solution**: Split into modular views (Phase 1.1)

### 2. JWT in localStorage
**File**: `frontend/src/lib/api.ts`
**Issue**: 15 references to localStorage for token storage
**Solution**: Migrate to httpOnly cookies (Phase 1.3)

### 3. N+1 Query Risks
**Locations**:
- `chat()` - No select_related on user lookup
- `conversation_list()` - Messages accessed in loop
- `document_list()` - User not select_related

### 4. Missing Rate Limits
**Endpoints needing protection**:
- `/api/auth/login/` - Brute force risk
- `/api/auth/register/` - Spam risk
- `/api/chat/` - API cost risk
- `/api/documents/upload/` - Storage abuse

### 5. No API Versioning
**Current**: `/api/chat/`
**Target**: `/api/v1/chat/`

### 6. Synchronous Document Processing
**File**: `api/views.py:382`
**Code**: `process_document(str(doc.id))` called inline
**Issue**: Blocks request, risk of timeout
**Solution**: Celery async (Phase 1.10)

---

## 📦 Dependencies Status

### Backend (requirements.txt)
```
Django 5.x
Django REST Framework
djangorestframework-simplejwt
channels (WebSocket)
celery
django-cors-headers
psycopg2-binary (PostgreSQL)
openai
google-generativeai
groq
PyPDF2
python-docx
whoosh (search - to be replaced)
```

### Frontend (package.json)
```
next 15.1.0
react 18.3.1
framer-motion (installed)
sonner (installed)
axios
lucide-react
recharts
react-markdown
```

**Already Installed for Phase 1**:
- framer-motion ✓
- sonner ✓

**Need Installation**:
- vitest ✗
- @testing-library/react ✗
- cmdk ✗

---

## 🏗️ Database Models

### Core Models (from core/models.py)
- **User** - Django auth user
- **BusinessProfile** - Company info, avatar, goals, metrics
- **Conversation** - Chat sessions
- **Message** - Chat messages
- **Document** - Uploaded files with status
- **Task** - Task management
- **TaskActivity** - Task history
- **TaskAISuggestion** - AI-generated task suggestions
- **TaskAttachment** - File attachments on tasks
- **TaskTag** - Task categorization
- **DocumentChunk** - Text chunks for RAG

---

## 📋 Phase 1 Priorities

| Priority | Task | Complexity |
|----------|------|------------|
| **Critical** | Split api/views.py | Medium |
| **Critical** | API versioning /api/v1/ | Low |
| **Critical** | Refresh token rotation | High |
| **High** | Redis caching layer | Medium |
| **High** | N+1 query fixes | Low |
| **High** | Pagination everywhere | Low |
| **High** | Rate limiting | Medium |
| **Medium** | S3 file storage | Medium |
| **Medium** | Meilisearch migration | High |
| **Medium** | Celery async processing | Medium |
| **Low** | Real RAG pipeline | High |

---

## ✅ Pre-Overhaul Checklist

- [x] Branch created: `feat/overhaul-v2`
- [x] Tag created: `pre-overhaul-v1`
- [x] Audit snapshot generated
- [ ] Backend tooling installed
- [ ] Frontend tooling installed
- [ ] Verify all tests pass
- [ ] Verify build succeeds

---

## 📝 Notes

**Strengths**:
- Good model structure with proper relationships
- Already using logging (not print statements)
- Frontend has modern stack (Next.js 15, Tailwind 4, shadcn/ui)
- API structure is RESTful and well-organized (just needs splitting)

**Concerns**:
- 1172-line god view file needs immediate attention
- JWT security needs hardening (localStorage → httpOnly)
- Document processing is synchronous (will fail on large files)
- No Redis caching currently implemented
- Search uses Whoosh (needs Meilisearch for production)

---

*This snapshot captured the state of the codebase before the Phase 1 overhaul began.*
