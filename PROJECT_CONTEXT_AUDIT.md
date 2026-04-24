# AEIOU AI — COMPLETE PROJECT AUDIT & CONTEXT DOCUMENT
**Generated: 2024-04-24**  
**Purpose:** End-to-end codebase analysis for improvement planning

---

## 1. PROJECT OVERVIEW

### What This App Does
**AEIOU AI** is an AI-powered business assistant platform that helps small-to-medium business owners manage their operations through natural language conversations. It combines:

- **AI Chat Partner** (named "Aiden") — Conversational interface for business questions
- **Document Intelligence** — Upload, search, and analyze business documents
- **Task Management** — Kanban-style project management with AI assistance
- **Business Profile** — Centralized company context (metrics, goals, industry)
- **Memory System** — AI remembers user preferences and facts across sessions

### Target User
Solo entrepreneurs and small business owners who need a digital "Chief of Staff" to help organize documents, track tasks, and get business insights without managing multiple tools.

### Problem It Solves
Information fragmentation — business data scattered across emails, documents, spreadsheets, and notes. AEIOU AI centralizes everything and provides an AI interface to query and act on that data.

### "Aiden" — The AI Persona
**Aiden** (formerly just "AEIOU AI") is the named AI business partner:

| Attribute | Value |
|-----------|-------|
| **Name** | Aiden |
| **Role** | AI Business Partner & Chief of Staff |
| **Personality** | Professional, approachable, proactive, data-driven |
| **Voice** | Trusted senior advisor who knows the business intimately |
| **Key Rule** | NEVER says "As an AI..." — always speaks as "I (Aiden)" |

**Trigger Behaviors:**
- "I need to..." → Creates task automatically
- "Remind me to..." → Task with reminder
- "By Friday..." → Task with due date
- Mentions files/docs → Searches immediately without asking

### Business Model
**B2B SaaS** — Subscription-based:
- Free tier (limited documents/conversations)
- Pro tier (unlimited, advanced features)
- Enterprise tier (team collaboration, admin controls)

Currently in **MVP/late Alpha** — not production-ready for paying customers.

---

## 2. FOLDER STRUCTURE

```
AEIOU AI/
├── backend (Django)
│   ├── api/                    # REST API endpoints
│   │   ├── __init__.py
│   │   ├── urls.py            # URL routing (all endpoints)
│   │   ├── views.py           # Main view logic (1100+ lines - GOD FILE)
│   │   ├── auth_views.py      # Auth endpoints (register, login, etc)
│   │   ├── task_views.py      # Task management endpoints
│   │   ├── consumers.py       # WebSocket consumers (barely used)
│   │   ├── routing.py         # WebSocket routing
│   │   └── tests.py           # (likely empty)
│   │
│   ├── core/                   # Django models
│   │   ├── __init__.py
│   │   ├── models.py          # All 12 models (see section 3)
│   │   ├── admin.py           # Django admin config
│   │   ├── apps.py
│   │   └── migrations/        # Database migrations
│   │
│   ├── agents/                 # AI orchestration layer
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Main AI orchestrator (627 lines)
│   │   ├── prompts.py         # System prompts (Aiden persona)
│   │   ├── tool_decision.py   # Tool selection logic
│   │   └── entity_resolver.py # Entity resolution for tools
│   │
│   ├── services/               # AI services layer
│   │   ├── __init__.py
│   │   ├── model_layer.py     # Abstraction over AI providers
│   │   ├── gemini.py          # Google Gemini integration
│   │   ├── groq_service.py    # Groq API integration
│   │   ├── openrouter.py      # OpenRouter fallback
│   │   ├── document.py        # Document processing (PDF/DOCX/TXT)
│   │   └── search.py          # Document search (Whoosh-based)
│   │
│   ├── mcp/                    # Model Context Protocol tools
│   │   ├── __init__.py
│   │   ├── tools.py           # Tool definitions (1325 lines, 48 tools)
│   │   └── servers/           # (empty)
│   │
│   ├── config/                 # Django settings
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py        # Shared settings
│   │   │   ├── dev.py         # Development overrides
│   │   │   └── prod.py        # Production overrides
│   │   ├── urls.py            # Root URL config
│   │   ├── wsgi.py            # WSGI entry point
│   │   └── asgi.py            # ASGI entry point (WebSockets)
│   │
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── middleware.py      # Custom middleware
│   │   ├── logger.py          # Logging utilities
│   │   └── sanitization.py    # Input sanitization
│   │
│   ├── manage.py               # Django CLI
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment template
│   └── render.yaml            # Render.com deployment config
│
├── frontend (Next.js 15)
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   │   ├── page.tsx       # Landing/marketing page
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── globals.css    # Global styles
│   │   │   ├──
│   │   │   ├── chat/
│   │   │   │   └── page.tsx   # Main chat interface (900+ lines)
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx   # Analytics dashboard
│   │   │   ├── documents/
│   │   │   │   └── page.tsx   # Document list & upload
│   │   │   ├── tasks/
│   │   │   │   └── page.tsx   # Task management (Kanban)
│   │   │   ├── settings/
│   │   │   │   └── page.tsx   # User & business profile
│   │   │   ├── login/
│   │   │   │   └── page.tsx   # Login page
│   │   │   ├── register/
│   │   │   │   └── page.tsx   # Registration
│   │   │   ├── forgot-password/
│   │   │   │   └── page.tsx
│   │   │   ├── reset-password/
│   │   │   │   └── page.tsx
│   │   │   └── verify-email/
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/        # React components
│   │   │   ├── ui/            # shadcn/ui components (15 items)
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── client-layout.tsx        # Main app layout
│   │   │   ├── auth-guard.tsx           # Auth protection
│   │   │   ├── sidebar-new.tsx          # Navigation sidebar
│   │   │   ├── chat-context.tsx         # Chat state provider
│   │   │   ├── loading-context.tsx      # Loading state
│   │   │   ├── enhanced-command-palette.tsx  # Cmd+K palette
│   │   │   ├── kanban-board.tsx         # Task board
│   │   │   ├── notification-bell.tsx  # Notifications UI
│   │   │   ├── onboarding-wizard.tsx    # First-time setup
│   │   │   ├── error-boundary.tsx       # Error handling
│   │   │   └── ...
│   │   │
│   │   ├── lib/               # Utilities
│   │   │   ├── api.ts         # Axios client + interceptors
│   │   │   └── utils.ts       # Helper functions
│   │   │
│   │   └── hooks/             # Custom React hooks
│   │       └── use-toast.ts   # Toast notifications
│   │
│   ├── public/                # Static assets
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── docs/                      # Documentation
│   ├── PROJECT_VISION.md
│   ├── ARCHITECTURE.md
│   └── API_GUIDE.md
│
└── MIGRATE_TO_POSTGRES.md     # DB migration guide
```

---

## 3. DJANGO MODELS

### Model Summary (12 models across 5 domains)

#### AUTHENTICATION (2 models)
```python
EmailVerification
├── user: OneToOneField(User)
├── code: CharField(6)
├── created_at: DateTimeField(auto_now_add)
├── is_verified: BooleanField(default=False)
└── attempts: IntegerField(default=0)
# Meta: indexes on [code, created_at]
# Methods: is_expired(), is_locked(), record_attempt()

PasswordResetCode
├── user: ForeignKey(User)
├── code: CharField(6)
├── created_at: DateTimeField(auto_now_add)
├── is_used: BooleanField(default=False)
└── attempts: IntegerField(default=0)
# Meta: ordering [-created_at], indexes [code, created_at]
# Methods: is_expired(), clean_expired_codes()
```

#### BUSINESS PROFILE (1 model)
```python
BusinessProfile
├── user: OneToOneField(User, related_name="business_profile")
├── company_name: CharField(255, blank)
├── industry: CharField(100, blank)
├── company_size: CharField(50, blank)  # e.g., "10-50"
├── website: URLField(255, blank)
├── description: TextField(blank)
├── goals: JSONField(default=list)       # ["increase revenue", ...]
├── key_metrics: JSONField(default=dict) # {"revenue": 50000, ...}
├── avatar: ImageField(upload_to="avatars/%Y/%m/", null=True)
├── created_at: DateTimeField(auto_now_add)
└── updated_at: DateTimeField(auto_now)
# Purpose: Business context for AI personalization
```

#### AI MEMORY (1 model)
```python
UserMemory
├── user: ForeignKey(User, related_name="memories")
├── category: CharField(choices=[preference, decision, context, fact, followup])
├── key: CharField(100, db_index=True)  # e.g., "preferred_report_format"
├── value: TextField()                   # e.g., "bullet points with numbers"
├── source_conversation: UUIDField(null=True)
├── created_at: DateTimeField(auto_now_add)
└── updated_at: DateTimeField(auto_now)
# Meta: unique_together (user, key), indexes [user, category]
# Purpose: Structured facts AI remembers about user
```

#### DOCUMENTS (2 models)
```python
Document
├── id: UUIDField(primary_key, default=uuid4)
├── user: ForeignKey(User, related_name="documents")
├── title: CharField(255)
├── file: FileField(upload_to="documents/%Y/%m/")
├── file_type: CharField(10)  # pdf, docx, txt
├── summary: TextField(blank)  # AI-generated summary
├── status: CharField(choices=[pending, processing, ready, failed])
├── page_count: IntegerField(default=0)
└── created_at: DateTimeField(auto_now_add)
# Meta: indexes [user, status, -created_at], [user, file_type]

DocumentChunk
├── document: ForeignKey(Document, related_name="chunks")
├── chunk_index: IntegerField()
├── content: TextField()
├── page_number: IntegerField(default=0)
├── keywords: JSONField(default=list)  # Extracted for search
# Meta: ordering [chunk_index], indexes [document, chunk_index], [keywords]
# Purpose: Searchable chunks for RAG (Retrieval Augmented Generation)
```

#### CONVERSATIONS (2 models)
```python
Conversation
├── id: UUIDField(primary_key, default=uuid4)
├── user: ForeignKey(User, related_name="conversations")
├── title: CharField(255, blank)
├── created_at: DateTimeField(auto_now_add)
└── updated_at: DateTimeField(auto_now)
# Meta: ordering [-updated_at], indexes [user, -updated_at]

Message
├── conversation: ForeignKey(Conversation, related_name="messages")
├── role: CharField(choices=[user, assistant, tool])
├── content: TextField()
├── tool_calls: JSONField(null=True)   # Tool requests made
├── tool_results: JSONField(null=True)  # Tool responses
├── model_used: CharField(50, blank)    # gemini/groq/openrouter
└── created_at: DateTimeField(auto_now_add)
# Meta: ordering [created_at]
```

#### TASK MANAGEMENT (4 models)
```python
Task
├── id: UUIDField(primary_key, default=uuid4)
├── user: ForeignKey(User, related_name="tasks")
├── title: CharField(255)
├── description: TextField(blank)
├── status: CharField(choices=[todo, in_progress, review, done, archived])
├── priority: CharField(choices=[low, medium, high, urgent])
├── due_date: DateTimeField(null=True)
├── created_by: ForeignKey(User, related_name="created_tasks")
├── assignee: ForeignKey(User, null=True, related_name="assigned_tasks")
├── conversation: ForeignKey(Conversation, null=True, related_name="tasks")
├── business_profile: ForeignKey(BusinessProfile, related_name="tasks")
├── estimated_hours: DecimalField(5,2, null=True)
├── actual_hours: DecimalField(5,2, null=True)
├── completion_notes: TextField(blank)
├── is_subtask: BooleanField(default=False)
├── parent_task: ForeignKey("self", null=True, related_name="subtasks")
├── created_at: DateTimeField(auto_now_add)
├── updated_at: DateTimeField(auto_now)
├── completed_at: DateTimeField(null=True)
└── archived_at: DateTimeField(null=True)
# Meta: ordering [-created_at], 5 strategic indexes

TaskTag
├── task: ForeignKey(Task, related_name="tags")
├── tag: CharField(100)
└── created_at: DateTimeField(auto_now_add)
# Meta: unique_together (task, tag)

TaskComment
├── id: UUIDField(primary_key, default=uuid4)
├── task: ForeignKey(Task, related_name="comments")
├── user: ForeignKey(User)
├── content: TextField()
├── created_at: DateTimeField(auto_now_add)
└── updated_at: DateTimeField(auto_now)
# Meta: ordering [-created_at]

TaskActivity  # Audit trail
├── id: UUIDField(primary_key, default=uuid4)
├── task: ForeignKey(Task, related_name="activities")
├── user: ForeignKey(User)
├── activity_type: CharField(choices=[created, updated, status_changed, ...])
├── old_value: TextField(blank)
├── new_value: TextField(blank)
└── created_at: DateTimeField(auto_now_add)
# Meta: ordering [-created_at]

TaskAttachment
├── task: ForeignKey(Task, related_name="attachments")
├── document: ForeignKey(Document)
└── attached_at: DateTimeField(auto_now_add)
# Meta: unique_together (task, document)

TaskAISuggestion
├── id: UUIDField(primary_key, default=uuid4)
├── user: ForeignKey(User, related_name="task_suggestions")
├── suggested_title: CharField(255)
├── suggested_description: TextField(blank)
├── suggested_priority: CharField(default="medium")
├── suggested_due_date: DateTimeField(null=True)
├── source_type: CharField(100)  # chat, document, email_pattern
├── source_id: CharField(255)   # conversation_id or document_id
├── source_content: TextField()  # Trigger text
├── confidence_score: DecimalField(3,2, null=True)
├── was_accepted: BooleanField(null=True)
├── created_task: ForeignKey(Task, null=True, related_name="ai_suggestion")
└── created_at: DateTimeField(auto_now_add)
# Meta: ordering [-created_at]
```

#### NOTIFICATIONS (1 model)
```python
Notification
├── user: ForeignKey(User, related_name="notifications")
├── message: TextField()
├── priority: CharField(choices=[low, normal, high, urgent], default="normal")
├── is_read: BooleanField(default=False, db_index=True)
├── action_url: CharField(500, blank)
└── created_at: DateTimeField(auto_now_add, db_index=True)
# Meta: ordering [-created_at], indexes [user, is_read, -created_at]
```

---

## 4. API ENDPOINTS

### Complete API Map (60 endpoints across 8 domains)

#### HEALTH & DEMO (2)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/health/` | No | Status check for load balancers |
| POST | `/api/demo/seed/` | Yes | Generate demo data |

#### AUTHENTICATION (6)
| Method | Path | Auth | Purpose | Request | Response |
|--------|------|------|---------|---------|----------|
| POST | `/api/auth/register/` | No | Register new user | {email, password, username} | {user, tokens} |
| POST | `/api/auth/login/` | No | Login | {email, password} | {access_token, refresh_token, user} |
| POST | `/api/auth/verify-email/` | No | Verify 6-digit code | {email, code} | {success} |
| POST | `/api/auth/resend-verification/` | No | Resend code | {email} | {success} |
| POST | `/api/auth/forgot-password/` | No | Request reset | {email} | {success} |
| POST | `/api/auth/verify-reset-code/` | No | Verify reset code | {email, code} | {success} |
| POST | `/api/auth/reset-password/` | No | Set new password | {email, code, new_password} | {success} |

#### CHAT (4)
| Method | Path | Auth | Purpose | Notes |
|--------|------|------|---------|-------|
| POST | `/api/chat/` | Yes | Non-streaming chat | JSON response |
| POST | `/api/chat/stream/` | Yes | Streaming chat (SSE) | Server-Sent Events |
| GET | `/api/conversations/` | Yes | List user's chats | Pagination |
| GET | `/api/conversations/{id}/` | Yes | Get chat history | |
| GET | `/api/conversations/{id}/export/` | Yes | Export as text | |
| POST | `/api/conversations/{id}/delete/` | Yes | Soft delete | |

#### DOCUMENTS (7)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/documents/` | Yes | List documents |
| POST | `/api/documents/upload/` | Yes | Upload file | Multipart/form-data |
| GET | `/api/documents/{id}/status/` | Yes | Check processing status |
| POST | `/api/documents/{id}/delete/` | Yes | Delete document |
| GET | `/api/documents/{id}/summary/` | Yes | Get AI summary |
| POST | `/api/documents/{id}/reindex/` | Yes | Rebuild search index |

#### BUSINESS PROFILE (2)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET/POST/PUT | `/api/profile/` | Yes | Get/update profile |
| GET | `/api/analytics/` | Yes | Business dashboard data |

#### USER MANAGEMENT (3)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/user/update-username/` | Yes | Change username |
| POST | `/api/user/update-password/` | Yes | Change password |
| GET | `/api/user/info/` | Yes | Get current user |

#### TASKS (16)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/tasks/` | Yes | List tasks (filters: status, priority) |
| POST | `/api/tasks/create/` | Yes | Create task |
| GET | `/api/tasks/{id}/` | Yes | Get task details |
| PUT | `/api/tasks/{id}/update/` | Yes | Update task |
| POST | `/api/tasks/{id}/delete/` | Yes | Delete task |
| POST | `/api/tasks/{id}/complete/` | Yes | Mark done |
| POST | `/api/tasks/{id}/reopen/` | Yes | Mark not done |
| GET | `/api/tasks/{id}/comments/` | Yes | List comments |
| POST | `/api/tasks/{id}/comments/create/` | Yes | Add comment |
| POST | `/api/tasks/{id}/comments/{cid}/delete/` | Yes | Delete comment |
| GET | `/api/tasks/{id}/activities/` | Yes | View audit trail |
| GET | `/api/tasks/dashboard/` | Yes | Dashboard stats |
| GET | `/api/tasks/stats/` | Yes | Aggregated metrics |
| POST | `/api/tasks/extract/` | Yes | AI extract from text |
| POST | `/api/tasks/suggestions/{id}/accept/` | Yes | Accept AI suggestion |
| POST | `/api/tasks/suggestions/{id}/reject/` | Yes | Reject AI suggestion |

#### TAGS (4)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET/POST | `/api/tags/` | Yes | List/create tags |
| GET | `/api/tags/{name}/tasks/` | Yes | Tasks by tag |
| POST | `/api/tasks/{id}/tags/add/` | Yes | Tag a task |
| POST | `/api/tasks/{id}/tags/remove/` | Yes | Untag a task |

#### ONBOARDING (2)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/onboarding/status/` | Yes | Check completion |
| POST | `/api/onboarding/complete/` | Yes | Mark complete |

#### ADMIN (3)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/admin/dashboard/` | Yes | Admin stats |
| POST | `/api/admin/broadcast/` | Yes | Send notification to all |
| POST | `/api/admin/reindex-all/` | Yes | Reindex all documents |

#### NOTIFICATIONS (2)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/notifications/` | Yes | List notifications |
| POST | `/api/notifications/{id}/read/` | Yes | Mark as read |

---

## 5. FRONTEND PAGES & COMPONENTS

### Page Structure (Next.js App Router)

#### PUBLIC ROUTES (no auth required)
| Route | File | Renders |
|-------|------|---------|
| `/` | `page.tsx` | Marketing landing page |
| `/login` | `login/page.tsx` | Login form |
| `/register` | `register/page.tsx` | Registration form |
| `/forgot-password` | `forgot-password/page.tsx` | Password reset request |
| `/reset-password` | `reset-password/page.tsx` | New password form |
| `/verify-email` | `verify-email/page.tsx` | Email verification |

#### PROTECTED ROUTES (auth required)
| Route | File | Renders | Layout |
|-------|------|---------|--------|
| `/chat` | `chat/page.tsx` | Main chat interface | Sidebar |
| `/chat?id={uuid}` | `chat/page.tsx` | Specific conversation | Sidebar |
| `/dashboard` | `dashboard/page.tsx` | Analytics dashboard | Sidebar |
| `/documents` | `documents/page.tsx` | Document list & upload | Sidebar |
| `/tasks` | `tasks/page.tsx` | Kanban task board | Sidebar |
| `/settings` | `settings/page.tsx` | Profile & preferences | Sidebar |

### Key Components

#### LAYOUT & NAVIGATION
| Component | Purpose | Props |
|-----------|---------|-------|
| `client-layout.tsx` | App shell, providers | {children} |
| `auth-guard.tsx` | Route protection | {children} |
| `sidebar-new.tsx` | Navigation, recent chats | - |
| `loading-context.tsx` | Global loading state | - |
| `error-boundary.tsx` | Crash recovery | {children} |

#### CHAT SYSTEM
| Component | Purpose |
|-----------|---------|
| `chat-context.tsx` | Chat state management |
| `enhanced-command-palette.tsx` | Cmd+K quick actions |
| `typing-indicator.tsx` | "Aiden is typing..." animation |
| `loading-skeletons.tsx` | Loading placeholders |
| `onboarding-wizard.tsx` | First-time user flow |

#### UI COMPONENTS (shadcn/ui base)
Located in `components/ui/`:
- Button, Card, Input, Dialog, Dropdown, Badge, Avatar, Select, Textarea, Tabs, Table, Toast, etc.

#### CUSTOM COMPONENTS
| Component | Purpose |
|-----------|---------|
| `kanban-board.tsx` | Drag-drop task board |
| `notification-bell.tsx` | Real-time notification UI |
| `floating-notification-widget.tsx` | Toast-style notifications |
| `sound-effects.tsx` | Audio feedback |
| `toaster.tsx` | Sonner toast wrapper |

---

## 6. CURRENT STATE OF KEY FEATURES

### CHAT SYSTEM

**How it works:**
1. User types message → POST to `/api/chat/stream/`
2. Backend orchestrator classifies intent (search/document/analytics/action/task)
3. Orchestrator builds execution plan (which tools to call)
4. Tools execute in sequence (business profile, documents, tasks, etc)
5. AI synthesizes response based on tool results
6. Response streamed back via Server-Sent Events (SSE)
7. Frontend displays streaming tokens + "thinking" indicators
8. Full response saved to Message model

**AI Model Pipeline:**
```
Gemini (streaming) → Groq (fallback) → OpenRouter (last resort)
```

**Prompt Structure:**
```python
SYSTEM: BUSINESS_ASSISTANT_SYSTEM_PROMPT  # Aiden persona
CONTEXT: User profile + memory + conversation history (last 20)
TOOLS: Dynamic based on intent (get_business_profile, list_documents, etc)
SYNTHESIS: Tool results formatted for natural response
```

**Current Issues:**
- No true RAG — document chunks searched by keywords, not embeddings
- Context limited to 20 messages
- No conversation branching/forking
- AI sometimes hallucinates despite "NEVER hallucinate" rules

### DOCUMENTS

**Upload Flow:**
1. User selects file → POST to `/api/documents/upload/`
2. File saved to `MEDIA_ROOT/documents/YYYY/MM/`
3. Document record created (status: "pending")
4. **(Sync processing)** Text extracted based on type:
   - PDF: `pypdf.PdfReader`
   - DOCX: `python-docx`
   - TXT: Direct read
5. Text chunked into ~1500 char segments
6. Keywords extracted from each chunk (simple NLP)
7. Document status → "ready"

**Search:**
- Uses Whoosh (pure Python search library)
- Searches across: title, summary, chunk content, keywords
- No vector similarity search
- Single-node only (no distributed search)

**Chat Integration:**
- User asks about documents
- Orchestrator calls `search_documents` tool
- Returns top matches
- AI references in response

### TASKS

**Data Shape:**
```typescript
{
  id: UUID,
  title: string,
  description: string,
  status: "todo" | "in_progress" | "review" | "done" | "archived",
  priority: "low" | "medium" | "high" | "urgent",
  due_date: ISO8601 | null,
  assignee: User | null,
  tags: string[],
  subtasks: Task[],
  comments: Comment[],
  activities: Activity[],
  estimated_hours: number,
  actual_hours: number,
  created_at: ISO8601
}
```

**Workflow:**
1. User creates task manually OR AI suggests from chat
2. Kanban board displays by status columns
3. Drag to change status (UI only, no backend drag endpoint)
4. Comments for collaboration
5. Activity log tracks all changes

**AI Integration:**
- `extract_tasks_from_text` endpoint parses natural language
- Example: "I need to call John by Friday" → Task with title + due date
- Suggestions stored in `TaskAISuggestion` for user approval

### AUTH FLOW

**Registration:**
1. POST `/api/auth/register/` → User created (is_active=False)
2. 6-digit code generated, "sent" via console (email backend)
3. User enters code → POST `/api/auth/verify-email/`
4. User activated, JWT tokens returned

**Login:**
1. POST `/api/auth/login/` → Validate credentials
2. Return `{access_token, refresh_token, user}`
3. Frontend stores tokens in **localStorage** (security risk)
4. Axios interceptor adds `Authorization: Bearer {token}`

**Session:**
- Access token: Long-lived (no expiry check in code)
- No refresh token rotation
- No sliding sessions
- Auth state lost on hard refresh (reads from localStorage)

**Password Reset:**
1. POST `/api/auth/forgot-password/` → Code generated
2. Code verified via `/api/auth/verify-reset-code/`
3. New password set via `/api/auth/reset-password/`

---

## 7. ENVIRONMENT & CONFIGURATION

### Key Environment Variables

#### SECURITY
```bash
SECRET_KEY              # Django secret (auto-generated warning if missing)
DEBUG                   # True/False
ALLOWED_HOSTS           # Comma-separated domains
```

#### DATABASE
```bash
DATABASE_URL            # sqlite:///db.sqlite3 OR postgresql://...
```

#### AI PROVIDERS
```bash
GEMINI_API_KEY          # Google AI Studio
GEMINI_MODEL            # gemini-2.0-flash (default)
GROQ_API_KEY            # Groq console
GROQ_MODEL              # llama-3.1-8b-instant
OPENROUTER_API_KEY      # OpenRouter
OPENROUTER_MODEL        # meta-llama/llama-3.2-3b-instruct:free
```

#### OPTIONAL SERVICES
```bash
BRAVE_SEARCH_API_KEY    # Web search (2000 queries/month free)
REDIS_URL               # redis://localhost:6379/0
```

#### TIMEOUTS
```bash
GEMINI_TIMEOUT=15
GROQ_TIMEOUT=10
OPENROUTER_TIMEOUT=20
MAX_TOOL_ITERATIONS=6
```

#### DOCUMENT PROCESSING
```bash
MAX_UPLOAD_SIZE_MB=10
CHUNK_SIZE_CHARS=1500
MAX_CHUNKS_PER_DOC=20
```

#### PRODUCTION SECURITY
```bash
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

#### EMAIL
```bash
EMAIL_BACKEND           # console for dev, smtp for prod
EMAIL_HOST
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
```

#### STORAGE (R2 for production)
```bash
R2_ACCESS_KEY
R2_SECRET_KEY
R2_BUCKET_NAME
R2_ENDPOINT_URL         # https://<account>.r2.cloudflarestorage.com
```

#### FRONTEND
```bash
FRONTEND_URL=http://localhost:3000  # For CORS and email links
```

---

## 8. NOTABLE DESIGN DECISIONS & TECHNICAL DEBT

### UNIQUE DESIGN DECISIONS

#### 1. "No Vector DB" Philosophy
- Uses Whoosh + keyword search instead of embeddings
- Rationale: "Simpler, cheaper, good enough for MVP"
- Tradeoff: Won't scale past ~10k documents

#### 2. MCP (Model Context Protocol) Architecture
- Tools defined as JSON schema sent to LLM
- Orchestrator decides which tools to call
- Results synthesized into natural response
- Extensible: Add new tool → AI can use it immediately

#### 3. Hybrid AI Provider Strategy
- Primary: Gemini (Google, generous free tier)
- Fallback 1: Groq (fast, cheap)
- Fallback 2: OpenRouter (access to many models)
- Automatic failover on failure

#### 4. JSON-Based "Memory" (Not Vector)
- UserMemory stores structured key-value pairs
- Categories: preference, decision, context, fact, followup
- Unique per (user, key)
- Simple, reliable, no embedding costs

### TECHNICAL DEBT

#### CRITICAL
1. **No tests** — Zero unit, integration, or E2E tests
2. **No type checking** — Backend lacks mypy enforcement
3. **GOD FILE: api/views.py** — 1172 lines, 34 view functions
4. **Hydration issues** — React SSR/client mismatch (partially fixed)
5. **JWT in localStorage** — XSS vulnerability

#### HIGH
6. **SQLite in production path** — Database file will corrupt under load
7. **Synchronous document processing** — Upload blocks server
8. **No API versioning** — Breaking changes impossible
9. **Whoosh search** — Single-node, no horizontal scaling
10. **No Redis** — Cache uses Django's database cache (slow)

#### MEDIUM
11. **Magic numbers everywhere** — Timeouts, pagination sizes hardcoded
12. **No rate limiting on AI endpoints** — Could burn through API credits
13. **No request ID tracing** — Debugging distributed issues impossible
14. **Frontend bundle size unknown** — No bundle analysis
15. **Document processing errors swallowed** — `except: pass` patterns

### WORKAROUNDS IN PLACE

1. **Hydration safety timer** — Forces mount after 2s if stuck
2. **AuthGuard flash fix** — Shows loading overlay until auth confirmed
3. **Sidebar state default values** — Avoids SSR/client mismatch
4. **AI fallback chain** — Three providers for reliability
5. **Tool result caching** — 5-minute cache to reduce AI costs

---

## APPENDIX: FILE LOCATIONS REFERENCE

### Critical Files
| Purpose | Path |
|---------|------|
| Main entry | `/api/views.py` |
| Models | `/core/models.py` |
| URL routing | `/api/urls.py` |
| AI orchestrator | `/agents/orchestrator.py` |
| System prompts | `/agents/prompts.py` |
| Tool definitions | `/mcp/tools.py` |
| Model layer | `/services/model_layer.py` |
| Chat page | `/frontend/src/app/chat/page.tsx` |
| API client | `/frontend/src/lib/api.ts` |
| Layout | `/frontend/src/components/client-layout.tsx` |

### Configuration
| Purpose | Path |
|---------|------|
| Environment template | `/.env.example` |
| Django base settings | `/config/settings/base.py` |
| Render deployment | `/render.yaml` |
| Requirements | `/requirements.txt` |

---

**Document Version:** 1.0  
**Generated By:** Code Analysis Subagent  
**Audit Status:** COMPLETE
