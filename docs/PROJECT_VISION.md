# AEIOU Business Assistant - Project Vision & Gap Analysis

## 1. Project Vision

### What It Is
AEIOU is an AI-powered business assistant that helps small-to-medium business owners manage their operations through natural conversation. It combines document intelligence, task management, and business analytics in one unified interface.

### Core User Interactions
1. **Chat-First Interface** - Users ask questions naturally; the AI responds with relevant data from their business context
2. **Document Management** - Upload contracts, reports, invoices; get summaries and answers without reading full documents
3. **Task Tracking** - Create, prioritize, and track business tasks with AI-suggested actions
4. **Analytics & Insights** - View business metrics and get AI-generated recommendations
5. **Memory Persistence** - The AI remembers preferences, decisions, and context across sessions

### Problem It Solves
Business owners waste time:
- Searching through scattered documents for information
- Forgetting decisions and context from previous discussions
- Manually tracking tasks without intelligent prioritization
- Paying for expensive RAG/vector DB infrastructure they don't need

AEIOU solves this with a **ragless architecture** - structured storage, keyword search, and intelligent orchestration instead of expensive embeddings.

---

## 2. Architecture (Current vs Ideal)

### Current State ✅
| Component | Technology | Status |
|-----------|-----------|--------|
| Frontend | Next.js 14 + TypeScript + Tailwind | Implemented |
| Backend | Django 5 + DRF | Implemented |
| Database | SQLite (dev) / PostgreSQL (prod) | Configured |
| Auth | JWT + dj-rest-auth | Working |
| AI Models | Gemini + Groq fallback | Implemented |
| File Storage | Local filesystem (dev) / S3 (prod) | Configured |

### Ideal MCP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MCP (Model Context Protocol) Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Orchestrator │  │ Tool Registry│  │ Memory Store │     │
│  │              │  │              │  │              │     │
│  │ • Intent     │  │ • 15+ Tools  │  │ • Structured │     │
│  │   Classification│ • Typed I/O │  │   Memory     │     │
│  │ • Planning   │  │ • Execution  │  │ • User       │     │
│  │ • Execution  │  │ • Validation │  │   Context    │     │
│  │ • Response   │  │              │  │              │     │
│  │   Synthesis  │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Task Manager (Auto-extraction + Lifecycle)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ragless Approach (Internal Knowledge First)

**Current:** Uses keyword-based document search + web search fallback

**Ideal:** Three-tier knowledge hierarchy:

1. **Tier 1 - Structured Memory** (Always checked first)
   - User preferences, business profile, key decisions
   - Stored in `UserMemory` table with categories
   - Fast SQL queries, no embeddings

2. **Tier 2 - Document Chunks** (Checked when documents are referenced)
   - Pre-chunked documents with keyword metadata
   - Keyword search across chunks
   - Summaries for quick reference

3. **Tier 3 - Web Search** (Only when explicit or nothing found)
   - Brave Search API
   - Marked as external in responses
   - Never hallucinate - clearly state "I searched the web for this"

---

## 3. User Experience (Ideal State)

### Navigation Philosophy
- **No broken routes** - Every navigation works, state persists
- **Smooth transitions** - Framer Motion page transitions, consistent loading screens
- **Context preservation** - Chat state survives navigation, page reloads
- **Command palette** - Cmd+K for quick actions, always available

### Data Presentation
- **Progressive disclosure** - Summary first, details on demand
- **Visual hierarchy** - Important metrics prominent, history collapsible
- **Consistent empty states** - Helpful guidance, not dead ends
- **Real-time updates** - Task status, document processing, new messages

### Error Handling
- **Graceful degradation** - AI service down? Show cached data + polite message
- **User-friendly messages** - No stack traces, clear next steps
- **Retry with backoff** - Failed uploads, network issues auto-retry
- **Validation feedback** - Inline, immediate, actionable

### Loading States
- **Single, branded loading screen** - Gradient + floating logo, no white flashes
- **Skeleton screens** - For content areas, not spinners
- **Progress indicators** - Document uploads, long AI responses
- **Optimistic UI** - Messages appear immediately, update on confirmation

---

## 4. MCP / AI Features (Ideal State)

### Complete Tool Inventory

| Tool | Status | Responsibility |
|------|--------|--------------|
| `get_business_profile` | ✅ | Load user context at conversation start |
| `get_user_memory` | ✅ | Retrieve structured memory by category |
| `save_memory` | ✅ | Persist key facts, preferences, decisions |
| `list_documents` | ✅ | Show user's document library |
| `search_documents` | ✅ | Keyword search across documents |
| `get_document_summary` | ✅ | Quick doc overview without reading |
| `get_revenue_data` | ✅ | Extract metrics from business profile |
| `update_business_metrics` | ✅ | Update KPIs when user shares them |
| `get_followup_items` | ✅ | Check for pending tracked items |
| `get_conversation_insights` | ✅ | Pattern analysis across conversations |
| `brave_search` | ✅ | Web search fallback |
| `list_tasks` | ⚠️ | Show user's tasks |
| `get_task_insights` | ⚠️ | Productivity analysis |
| `create_task` | ❌ | Extract & create from conversation |
| `update_task` | ❌ | Mark complete, update status |
| `delete_task` | ❌ | Remove tasks |
| `get_calendar_events` | ❌ | Future: Google Calendar integration |
| `send_email` | ❌ | Future: Draft & send via user's email |

### Ragless Reasoning (Ideal Behavior)

**Example User Query:** *"What's my revenue target for Q3 and how am I tracking?"*

**Ideal AI Response Flow:**

1. **Intent Classification:** `analytics` (revenue question)
2. **Tool Execution:**
   ```
   1. get_business_profile(user_id) → {goals: ["Q3 revenue target: $100K"], key_metrics: {current_revenue: 65000}}
   2. get_revenue_data(user_id) → trend analysis
   ```
3. **Response (No Hallucination):**
   > "Your Q3 revenue target is $100K, set on July 1st. You're currently at $65K (65% of target). Based on your monthly average of $21K, you're on track to hit ~$84K by quarter end - $16K short of goal. Want me to suggest ways to close the gap?"

**What Makes It Ragless:**
- ✅ No vector embeddings
- ✅ No "context chunks" passed to LLM
- ✅ Structured data queried, synthesized into natural language
- ✅ If data missing: "I don't see a Q3 target set. What's your goal?"
- ✅ No made-up numbers, no generic advice

### Task Management (Ideal)

**Auto-extraction:** When user says "Remind me to call John tomorrow"
→ AI calls `create_task` automatically, confirms: "Got it - calling John tomorrow. Added to your tasks."

**Contextual Suggestions:** After documents uploaded:
> "I see you uploaded a contract. Should I create a task to review it before Friday?"

---

## 5. Security & Best Practices (Ideal)

### Input Validation & Sanitization
```python
# Current: Basic validation
# Ideal: Strict schema validation

from pydantic import BaseModel, validator

class TaskCreateInput(BaseModel):
    user_id: int
    title: str
    due_date: Optional[datetime]
    
    @validator('title')
    def sanitize_title(cls, v):
        # Strip HTML, limit length, check for injection
        return bleach.clean(v[:200], tags=[])
```

### Authentication & Authorization
| Layer | Current | Ideal |
|-------|---------|-------|
| Passwords | PBKDF2 | Argon2 (modern standard) |
| JWT | Simple | Refresh tokens, rotation, blacklist |
| Sessions | Basic | Device fingerprinting, geo-check |
| 2FA | None | TOTP via authenticator apps |
| API Rate Limits | Basic | Per-endpoint, per-user tiers |

### File Handling
- ✅ File type validation (PDF, DOCX, TXT only)
- ✅ Size limits (configurable, default 10MB)
- ✅ Virus scanning (ClamAV integration)
- ✅ Secure filenames (UUID, no original names in storage)
- ✅ No execution permissions on upload directories
- ⏳ Quarantine + approval for large files

### Web Security
| Threat | Protection |
|--------|------------|
| CSRF | Django's CSRF middleware + double-submit cookies |
| XSS | Template escaping, Content-Security-Policy |
| SQL Injection | ORM usage (no raw SQL), parameterized queries |
| SSRF | URL validation on web search, whitelist domains |
| Clickjacking | X-Frame-Options: DENY |
| HSTS | Strict-Transport-Security header |

### Logging & Monitoring
```python
# Ideal: Structured logging with correlation IDs
logger.info("task_created", extra={
    "user_id": user_id,
    "task_id": task.id,
    "source": "ai_extraction",  # vs "manual"
    "correlation_id": request.headers.get("X-Request-ID")
})
```

- **Error tracking:** Sentry integration
- **Performance:** APM for slow queries
- **Security:** Failed auth attempts logged, alerted
- **Audit trail:** All data modifications tracked

---

## 6. Performance & Maintainability (Ideal)

### Database Optimization

**Current:** Basic indexing
```python
# Current
indexes = [models.Index(fields=["user", "category"])]
```

**Ideal:** Query-optimized schema
```python
# Ideal - Composite indexes for common queries
class Meta:
    indexes = [
        models.Index(fields=["user", "category", "-created_at"]),  # Memory retrieval
        models.Index(fields=["user", "status", "-updated_at"]),    # Active tasks
        models.Index(fields=["document", "keywords"], opclass=["gin"]),  # Doc search
    ]
    
# Partitioning for scale
class Task(models.Model):
    class Meta:
        db_table = "tasks_partitioned"
        
# Read replicas for analytics queries
```

### Caching Strategy

| Data Type | Cache Layer | TTL | Invalidation |
|-----------|-------------|-----|--------------|
| Business Profile | Redis | 5 min | On save |
| User Memory | Redis | 1 min | On write |
| Document Summaries | Redis | 10 min | On re-process |
| Conversation List | Session | N/A | On new message |
| Web Search | Redis | 1 hour | Never (idempotent) |
| AI Responses | Redis | 30 min | Never (cache key = hash of tools+query) |

### Code Quality

**Current:** Functional but mixed patterns
**Ideal:** Strict consistency

```python
# Service Layer Pattern (Ideal)
class TaskService:
    @staticmethod
    def create_from_conversation(user_id: int, text: str, ai_metadata: dict) -> Task:
        """
        Extract task from conversation and create.
        
        Args:
            user_id: The user creating the task
            text: Raw conversation text to extract from
            ai_metadata: Intent classification from AI
            
        Returns:
            Created Task instance
            
        Raises:
            TaskExtractionError: If no actionable task found
        """
        # Implementation
        pass

# No logic in views - only HTTP handling
def task_create_view(request):
    task = TaskService.create_from_conversation(...)
    return Response(TaskSerializer(task).data)
```

### Testing Strategy (Ideal)
```
├── tests/
│   ├── unit/              # Fast, isolated, mocking external services
│   ├── integration/       # DB interactions, API contracts
│   ├── e2e/              # Playwright tests for critical flows
│   └── mcp/              # Tool execution tests
```

### Dependency Philosophy
**Current:** Moderate dependencies
**Ideal:** Minimal, audited stack

| Purpose | Current | Ideal |
|---------|---------|-------|
| AI | gemini, groq | Same (necessary) |
| Search | requests | Same (simple) |
| Files | PyPDF2, python-docx | Same (domain-specific) |
| Cache | django-redis | Same (standard) |
| Validation | None | pydantic (strict typing) |
| Security | None extra | bleach, python-jose |

### Deployment Readiness

**Current:** Render config exists
**Ideal:** Multi-environment, automated

```yaml
# render.yaml (ideal state)
services:
  - type: web
    name: aeiou-api
    env: python
    plan: standard
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: aeiou-prod
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: aeiou-cache
          property: connectionString
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
    healthCheckPath: /api/health/
    autoDeploy: true
    
  - type: static
    name: aeiou-frontend
    buildCommand: cd frontend && npm ci && npm run build
    publishDir: frontend/dist
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=31536000, immutable
```

---

## 7. Ideal Feature Checklist

### MCP / Core Intelligence
| Feature | Status | Gap |
|---------|--------|-----|
| Intent classification | ✅ Implemented | - |
| Tool registry (15+ tools) | ⚠️ Partial (10 working, 4 missing) | Add CRUD task tools |
| Memory persistence | ✅ Working | - |
| Auto task extraction | ❌ Missing | Big gap - should extract from chat |
| Follow-up tracking | ✅ Working | - |
| Ragless responses | ⚠️ Working but needs tuning | Better synthesis prompts |
| Streaming responses | ✅ Working | - |
| Multi-step reasoning | ✅ Working | - |

### Frontend / UX
| Feature | Status | Gap |
|---------|--------|-----|
| Smooth navigation | ⚠️ Implemented, bugs fixed | Verify no white flash |
| Chat state persistence | ✅ Working (sessionStorage) | - |
| Input persistence | ✅ Working (localStorage) | - |
| Loading screens | ⚠️ Implemented, refining | Single loader verified |
| Command palette | ✅ Working | - |
| Document upload | ✅ Working | - |
| Task board | ✅ Implemented | Connect to auto-extraction |
| Responsive design | ✅ Working | - |
| Dark mode | ❌ Missing | Nice-to-have |

### Security
| Feature | Status | Gap |
|---------|--------|-----|
| Input sanitization | ⚠️ Basic | Add bleach for all user input |
| Rate limiting | ⚠️ Basic | Add tiered limits |
| File scanning | ❌ Missing | Add ClamAV |
| Audit logging | ⚠️ Basic | Structured logging |
| 2FA | ❌ Missing | Future feature |

### Performance
| Feature | Status | Gap |
|---------|--------|-----|
| DB indexing | ⚠️ Basic | Composite indexes |
| Query optimization | ⚠️ Needs profiling | Add query analyzer |
| Caching layer | ✅ Redis configured | Tune TTLs |
| CDN for assets | ✅ Via Render | - |
| Image optimization | ❌ Missing | Add next/image |

---

## 8. Example Scenarios (Ideal vs Current)

### Scenario 1: User Asks About Themselves

**User:** *"What's my company again?"*

**Ideal Response:**
> "You're running TechStart Solutions, a SaaS company in the fintech space with 12 employees. You mentioned wanting to expand to the EU market last month - how's that going?"

**Current Gap:** May respond generically if memory not fetched properly. Need to ensure `get_business_profile` + `get_user_memory` are always called for context.

---

### Scenario 2: Query Not in Memory

**User:** *"When did I hire Sarah?"*

**Ideal Response:**
> "I don't have that in your records. Would you like me to save that Sarah joined the team, and when?"

**Current Gap:** May hallucinate or say "I don't know" without offering to save. Need explicit "not found" handling + memory save suggestion.

---

### Scenario 3: Document Query

**User:** *"What did the vendor contract say about payment terms?"*

**Ideal Response:**
> "In your Acme Vendor Contract (uploaded Jan 15), Section 4.2 states: 'Payment is due Net 30 days from invoice date. Late payments incur 1.5% monthly service charge.' Want me to create a task to review this before the next invoice?"

**Current:** Working via `search_documents` → relevant chunks → synthesis. Gap: Should auto-suggest task creation for time-sensitive info.

---

### Scenario 4: Task Creation

**User:** *"I need to review the Q4 budget by Friday and send it to the team"*

**Ideal Response:**
> "Got it. I created two tasks:
> 1. Review Q4 budget (Due: Friday)
> 2. Send Q4 budget to team (Due: Friday)
> 
> They're in your 'High Priority' queue. Want me to remind you Thursday evening?"

**Current Gap:** Tasks must be created manually. Big feature gap: Auto-extraction from conversation.

---

## 9. Priority Gap Matrix

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Auto task extraction | High | Medium | **P1** |
| Task CRUD tools (create/update/delete) | High | Low | **P1** |
| Better synthesis prompts | High | Low | **P1** |
| Query optimization + indexing | Medium | Low | **P2** |
| Structured logging | Medium | Low | **P2** |
| Input sanitization (bleach) | Medium | Low | **P2** |
| File virus scanning | Low | Medium | P3 |
| 2FA | Low | High | P3 |
| Dark mode | Low | Low | P4 |

---

## 10. Next Steps (Recommended)

### Immediate (This Week)
1. **Add task CRUD tools** - `create_task`, `update_task`, `delete_task`
2. **Implement auto-extraction** - After intent classification, if task-related, extract and create
3. **Tune synthesis prompts** - Ensure "I don't know" is preferred over hallucination

### Short Term (Next 2 Weeks)
4. **Database optimization** - Add composite indexes, query profiling
5. **Structured logging** - Replace print statements, add correlation IDs
6. **Security hardening** - Input sanitization, rate limiting

### Medium Term (Next Month)
7. **Task management v2** - Calendar integration, recurring tasks, notifications
8. **Analytics dashboard** - Visual business metrics
9. **Mobile responsiveness** - Native-like mobile experience

### Long Term (Future)
10. **Multi-user teams** - Role-based access, shared documents
11. **Integrations** - Google Workspace, Slack, QuickBooks
12. **AI model flexibility** - Local models, custom fine-tuning

---

## Summary

**Current State:** Functional MVP with solid architecture. MCP orchestrator working, 10/15 tools implemented, ragless approach validated, UX mostly smooth with minor loading screen issues being resolved.

**Biggest Gaps:**
1. **Task auto-extraction** - Major UX win when AI creates tasks from chat
2. **Complete task CRUD** - Missing tools limit task management
3. **Synthesis tuning** - Need stricter "don't hallucinate" rules

**Architecture Strengths:**
- Clean separation (Frontend/Backend/MCP)
- No vector DB complexity (ragless works)
- Structured memory is fast and effective
- Tool-based architecture is extensible

**Ready for Scale:** With DB optimization and caching tuning, this architecture can handle thousands of users without re-architecting.
