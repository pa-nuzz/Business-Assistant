# AEIOU AI - Architecture Documentation

## Overview

AEIOU AI is a business assistant platform with task management, document processing, AI capabilities, and real-time collaboration features. Built with Django REST Framework (backend) and React/Next.js (frontend).

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENTS                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Web App    │  │  Mobile App  │  │  API Clients │                  │
│  │  (Next.js)   │  │  (Future)    │  │  (Zapier)    │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
└─────────┼─────────────────┼─────────────────┼──────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY / LOAD BALANCER                       │
│                         (Railway / AWS ALB)                              │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DJANGO APPLICATION                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     API LAYER (DRF)                               │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │
│  │  │  Auth   │ │ Tasks   │ │ Chat    │ │ Docs    │ │ Workspace│    │  │
│  │  │  Views  │ │  Views  │ │  Views  │ │  Views  │ │  Views   │    │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │  │
│  └───────┼───────────┼───────────┼───────────┼───────────┼──────────┘  │
│          ▼           ▼           ▼           ▼           ▼             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     SERVICE LAYER                                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │
│  │  │ AuthSvc │ │TaskSvc  │ │ChatSvc  │ │DocSvc   │ │Workspace│    │  │
│  │  │         │ │DetailSvc│ │         │ │         │ │Svc      │    │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │  │
│  └───────┼───────────┼───────────┼───────────┼───────────┼──────────┘  │
│          ▼           ▼           ▼           ▼           ▼             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     REPOSITORY / ORM LAYER                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │
│  │  │  User   │ │  Task   │ │Conversation│ │Document │ │Workspace│    │  │
│  │  │  Repo   │ │  Repo   │ │   Repo   │ │  Repo   │ │  Repo   │    │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │  │
│  └───────┼───────────┼───────────┼───────────┼───────────┼──────────┘  │
└──────────┼───────────┼───────────┼───────────┼───────────┼─────────────┘
           │           │           │           │           │
           ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  PostgreSQL  │  │    Redis     │  │   pgvector   │                  │
│  │  (Primary)   │  │  (Cache/     │  │  (Vector     │                  │
│  │              │  │   Sessions)  │  │   Search)    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Anthropic  │  │   OpenAI     │  │  Webhook     │                  │
│  │   (Claude)   │  │  (Embeddings)│  │  Endpoints   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: Django 5.x + Django REST Framework
- **Language**: Python 3.12+
- **Database**: PostgreSQL 16+ with pgvector extension
- **Cache**: Redis 7+
- **Authentication**: JWT (SimpleJWT) with refresh token rotation
- **API Documentation**: drf-spectacular (OpenAPI 3.0)
- **Task Queue**: Celery + Redis (for async operations)
- **Real-time**: Django Channels (WebSocket/SSE)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context + SWR/TanStack Query
- **Real-time**: Server-Sent Events (SSE)

### Infrastructure
- **Staging**: Railway
- **Production**: AWS (ECS Fargate + RDS + ElastiCache)
- **CI/CD**: GitHub Actions
- **Monitoring**: Datadog / Prometheus + Grafana

## Core Domain Models

### User & Authentication
```
User
├── id (UUID)
├── email (unique)
├── username (unique)
├── password_hash
├── is_active
├── is_staff
├── date_joined
├── last_login
└── email_verified

Session
├── id (UUID)
├── user (FK)
├── refresh_token_hash
├── user_agent
├── ip_address
├── created_at
├── expires_at
└── revoked_at
```

### Workspace & Permissions (RBAC)
```
Workspace
├── id (UUID)
├── name
├── slug (unique)
├── owner (FK → User)
├── business_context (JSON)
├── preferences (JSON)
├── created_at
└── updated_at

WorkspaceMember
├── id (UUID)
├── workspace (FK)
├── user (FK)
├── role (owner|admin|member|viewer)
├── invited_by (FK)
├── joined_at
└── UNIQUE(workspace, user)

WorkspaceInvitation
├── id (UUID)
├── workspace (FK)
├── email
├── role
├── invited_by (FK)
├── token (unique)
├── expires_at
├── accepted_at
└── revoked_at
```

### Tasks & Collaboration
```
Task
├── id (UUID)
├── workspace (FK)
├── title
├── description
├── status (todo|in_progress|review|done|archived)
├── priority (low|medium|high|urgent)
├── assignee (FK → User, nullable)
├── creator (FK → User)
├── parent_task (FK → Task, nullable)
├── due_date
├── completed_at
├── created_at
├── updated_at

TaskCollaborator
├── id (UUID)
├── task (FK)
├── user (FK)
├── added_by (FK)
├── added_at
└── UNIQUE(task, user)

TaskComment
├── id (UUID)
├── task (FK)
├── user (FK)
├── content
├── parent_comment (FK → TaskComment, nullable)
├── created_at
├── updated_at

TaskActivity
├── id (UUID)
├── task (FK)
├── user (FK)
├── action (created|updated|assigned|commented|...)
├── old_value (JSON)
├── new_value (JSON)
├── created_at
```

### Documents & RAG
```
Document
├── id (UUID)
├── workspace (FK)
├── title
├── file (FileField)
├── file_type
├── file_size
├── status (pending|processing|completed|failed)
├── extracted_text
├── summary
├── uploaded_by (FK → User)
├── created_at
├── updated_at

DocumentChunk
├── id (UUID)
├── document (FK)
├── chunk_index
├── content
├── embedding (vector, 1536 dims)
├── token_count
├── created_at

DocumentAnalysis
├── id (UUID)
├── document (FK, OneToOne)
├── insights (JSON)
├── extracted_tasks (JSON)
├── created_at
```

### Chat & Conversations
```
Conversation
├── id (UUID)
├── workspace (FK)
├── user (FK)
├── title
├── model_used
├── created_at
├── updated_at

Message
├── id (UUID)
├── conversation (FK)
├── role (user|assistant|system|tool)
├── content
├── tool_calls (JSON)
├── citations (JSON)
├── created_at

ConversationSummary
├── id (UUID)
├── conversation (FK, OneToOne)
├── summary_text
├── message_count
├── token_count
├── created_at
├── updated_at
```

### Memory (Long-term)
```
Memory
├── id (UUID)
├── workspace (FK)
├── user (FK, nullable)
├── content
├── embedding (vector, 1536 dims)
├── memory_type (fact|preference|procedure|context)
├── importance_score (0-1)
├── metadata (JSON)
├── created_at
├── updated_at
```

## API Design

### RESTful Conventions
- **Base Path**: `/api/v1/`
- **Authentication**: Bearer token (JWT)
- **Pagination**: Cursor-based (default 20, max 100)
- **Filtering**: Query parameters (`?status=todo&assignee=me`)
- **Sorting**: `?ordering=-created_at,title`
- **Errors**: RFC 7807 Problem Details format

### Endpoint Categories

| Category | Base Path | Key Endpoints |
|----------|-----------|---------------|
| Authentication | `/auth/` | `login`, `register`, `refresh`, `logout`, `verify-email` |
| Users | `/users/` | `me`, `profile`, `sessions`, `api-tokens` |
| Workspaces | `/workspaces/` | `list`, `create`, `retrieve`, `update`, `archive`, `members`, `invitations` |
| Tasks | `/tasks/` | `list`, `create`, `retrieve`, `update`, `delete`, `collaborators`, `comments`, `subtasks`, `time-entries` |
| Chat | `/conversations/` | `list`, `create`, `retrieve`, `delete`, `messages`, `stream` |
| Documents | `/documents/` | `list`, `upload`, `retrieve`, `download`, `reprocess`, `summary`, `analysis` |
| Search | `/search/` | `semantic`, `conversational`, `generate-embeddings` |
| Memory | `/memories/` | `list`, `create`, `retrieve`, `update`, `delete`, `regenerate-embeddings` |
| Notifications | `/notifications/` | `list`, `mark-read`, `preferences` |
| Webhooks | `/webhooks/` | `list`, `create`, `retrieve`, `update`, `delete`, `deliveries`, `test` |
| Analytics | `/analytics/` | `dashboard`, `workspace`, `engagement`, `export` |

### WebSocket / SSE Endpoints
- `/api/v1/chat/stream/` - Server-Sent Events for streaming chat responses
- `/api/v1/tasks/dashboard/stream/` - Real-time task updates

## Data Flow Patterns

### Chat with RAG Flow
```
1. User sends message → ConversationViewSet.chat()
2. Retrieve relevant document chunks via semantic search
3. Build context with conversation history + document chunks
4. Call Anthropic Claude with context
5. Stream response via SSE
6. Save assistant message with citations
7. Update conversation summary (async)
```

### Document Processing Flow
```
1. Upload document → DocumentViewSet.upload_document()
2. Save Document record with status=pending
3. Celery task: process_document(document_id)
   a. Extract text (pdfplumber, python-docx, etc.)
   b. Chunk text (semantic chunking)
   c. Generate embeddings (OpenAI text-embedding-3-small)
   d. Store chunks with pgvector
   e. Update Document status=completed
4. Webhook notification (optional)
```

### Task Assignment Flow
```
1. PATCH /tasks/{id}/ with assignee_id
2. TaskService.update_task()
3. Create TaskActivity record
4. Create Notification for assignee
5. Send real-time update via SSE/WebSocket
6. Email notification (async, if enabled)
```

## Security Architecture

### Authentication
- JWT access tokens (15 min expiry)
- Refresh tokens (7 days, rotated on use)
- Token blacklisting on logout
- Session tracking with device info

### Authorization (RBAC)
```
Workspace Roles:
├── Owner: Full access, can delete workspace, manage billing
├── Admin: Manage members, settings, all resources
├── Member: Create/edit tasks, documents, chat
└── Viewer: Read-only access

Resource-level permissions checked via PermissionService
```

### Data Protection
- Passwords: Argon2id hashing
- Secrets: Environment variables (never in code)
- PII: Encrypted at rest (PostgreSQL TDE)
- API tokens: Hashed storage (SHA-256)
- Rate limiting: Per-user, per-endpoint

### Network Security
- TLS 1.3 everywhere
- CORS: Restricted to known origins
- CSP headers
- HSTS
- Security headers via django-secure

## Caching Strategy

| Data Type | Cache Layer | TTL | Invalidation |
|-----------|-------------|-----|--------------|
| User sessions | Redis | 7 days | On logout/revoke |
| Workspace context | Redis | 1 hour | On update |
| Document chunks | Redis | 24 hours | On reprocess |
| Semantic search results | Redis | 30 min | On new documents |
| API responses (GET) | Redis | 5 min | On mutation |
| Embeddings | pgvector (disk) | Permanent | On regenerate |

## Async Processing (Celery)

### Task Queues
- `default`: General background tasks
- `documents`: Document processing (CPU intensive)
- `embeddings`: Embedding generation (API calls)
- `notifications`: Email, push, webhook delivery
- `analytics`: Report generation, exports
- `maintenance`: Cleanup, reindexing

### Scheduled Tasks
- Daily: Conversation summary generation
- Hourly: Expired invitation cleanup
- Weekly: Embedding regeneration (stale)
- Monthly: Analytics aggregation

## Monitoring & Observability

### Metrics
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Queue depths (Celery)
- Database query performance
- Cache hit rates
- Active WebSocket connections

### Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized: Datadog / ELK

### Health Checks
- `/health/` - Liveness probe
- `/health/ready/` - Readiness probe (DB, Redis, pgvector)
- `/health/startup/` - Startup probe

## Deployment Architecture

### Staging (Railway)
```
┌─────────────┐
│  Railway    │
│  ┌───────┐  │
│  │ Django │──► PostgreSQL (managed)
│  │ Worker │──► Redis (managed)
│  └───────┘  │
└─────────────┘
```

### Production (AWS)
```
┌────────────────────────────────────────────────────────────────┐
│                        AWS ACCOUNT                              │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │
│  │   ALB       │  │  ECS Fargate│  │  RDS PostgreSQL        │  │
│  │             │──►│  (Django)   │──►│  (Multi-AZ, pgvector)│  │
│  └─────────────┘  └─────────────┘  └────────────────────────┘  │
│         │                │                    │                 │
│         │         ┌──────┴──────┐            │                 │
│         │         │  ElastiCache│            │                 │
│         │         │  (Redis)    │            │                 │
│         │         └─────────────┘            │                 │
│         ▼                                    ▼                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Route 53 + ACM                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling
- Django: Stateless, scale via ECS tasks
- Celery: Scale workers per queue
- WebSocket: Sticky sessions or Redis pub/sub

### Database Optimization
- Read replicas for analytics queries
- Connection pooling (PgBouncer)
- Partitioning for large tables (TaskActivity, Message)
- Partial indexes for common filters

### Vector Search Scaling
- HNSW index on pgvector
- Consider dedicated vector DB (Pinecone, Weaviate) at scale
- Embedding caching in Redis

## Disaster Recovery

- **RPO**: 5 minutes (continuous WAL archiving)
- **RTO**: 30 minutes (automated failover)
- Backups: Daily snapshots + WAL archiving
- Cross-region replication for production

## Development Workflow

### Local Development
```bash
# Start services
docker-compose up -d

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver

# Frontend
cd frontend && npm run dev
```

### Testing
```bash
# Backend tests
python -m pytest core/tests/ -v

# Frontend tests
cd frontend && npm run test

# E2E tests
cd frontend && npm run e2e
```

### Code Quality
- **Linting**: ruff (Python), ESLint (TypeScript)
- **Formatting**: black (Python), prettier (TypeScript)
- **Type checking**: mypy (Python), tsc (TypeScript)
- **Pre-commit**: husky + lint-staged

## Future Considerations

1. **Multi-tenancy**: Current workspace model supports it; add row-level security
2. **Plugin System**: Webhook-based extensibility for custom integrations
3. **Mobile Apps**: React Native with shared TypeScript types
4. **Advanced AI**: Fine-tuned models, agent workflows, tool use
5. **Global Distribution**: Edge deployment for lower latency