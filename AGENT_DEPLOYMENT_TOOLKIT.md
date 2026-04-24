# AEIOU AI - Agent Deployment Toolkit

## Project Profile
- **Backend**: Django 5 REST API with PostgreSQL
- **Frontend**: Next.js 15 with TypeScript
- **Caching**: Redis
- **Architecture**: Service layer with event-driven communication
- **AI**: Multi-provider fallback (Gemini → Groq → OpenRouter)

---

## Execution Layers

### Layer 1: Core System (Must Run First)

**Components:**
1. **Django WSGI/ASGI Server** (config/wsgi.py, config/asgi.py)
   - Entry point for all HTTP/WebSocket requests
   - Must start before any agent can function

2. **Event Bus** (core/events/event_bus.py)
   - Initializes event subscriptions on startup
   - Required for all inter-service communication
   - Subscribes to: task.*, document.*, user.*, notification.*, message.*

3. **Redis Cache** (core/cache.py)
   - CacheService initialization
   - Required for user context caching and agent memory
   - TTL: 300s for user context, configurable for data

4. **Service Layer** (core/services/*)
   - AuthService, TaskService, DocumentService, ProfileService, ChatService, ConversationService, MessageService
   - Business logic foundation for all agent operations
   - Must be importable before agent initialization

**Startup Order:**
```
1. Django application loads
2. Event bus initializes (subscribes to all events)
3. Redis connection established
4. Service layer imports verified
5. Agent system ready
```

---

### Layer 2: Supporting Services (Run After Core)

**Components:**
1. **Model Router** (agents/router.py)
   - call_with_fallback() - Gemini → Groq → OpenRouter
   - call_with_fallback_stream() - Streaming with fallback
   - Requires: AI_CONFIG settings with API keys

2. **Model Layer** (services/model_layer.py)
   - call_model(), call_model_stream()
   - add_user_memory(), get_user_memory()
   - Requires: Router, Redis cache

3. **Document Processing** (services/document.py)
   - process_document() - Async document processing
   - Requires: Model layer, Model router

4. **Email Service** (services/email_service.py)
   - send_verification_email(), send_password_reset()
   - Requires: SMTP configuration

5. **Celery Workers** (services/tasks.py, config/celery.py)
   - Background task processing
   - Requires: Redis broker, Celery beat

**Startup Order:**
```
1. Router initializes (reads AI_CONFIG)
2. Model layer connects to router
3. Document processor ready
4. Email service configured
5. Celery workers start (if enabled)
```

---

### Layer 3: Optional Agents/Tools (Run On Demand)

**Components:**
1. **Orchestrator** (agents/orchestrator.py)
   - Main agent coordination
   - Multi-step reasoning chains
   - Context management
   - Requires: Model layer, Entity resolver, Tool decision engine

2. **Entity Resolver** (agents/entity_resolver.py)
   - Resolves "that document", "my task" references
   - Requires: Conversation history, user context

3. **Tool Decision Engine** (agents/tool_decision.py)
   - Decides which tools to call
   - Sequential/parallel execution planning
   - Requires: Tool definitions, query intent

4. **MCP Tools** (mcp/tools.py)
   - External tool integrations
   - Web scraping, search, etc.
   - Requires: Tool definitions, orchestrator

**Startup Order:**
```
1. Entity resolver initializes (per conversation)
2. Tool decision engine loads tool definitions
3. Orchestrator becomes available
4. MCP tools register with orchestrator
```

---

## Runtime Flow

### Synchronous Flow (HTTP Requests)

```
User Request → Django View → Service Layer → Model Layer → Router → AI Provider
                                    ↓
                              Event Bus Publish
                                    ↓
                              Cache Update
```

**Triggers:**
- API endpoint call (e.g., POST /api/v1/chat/)
- Authentication required (JWT)
- Rate limiting applied

**Execution:**
1. View validates request
2. Service executes business logic
3. If AI needed: Service → Model Layer → Router → AI Provider
4. Event published to event bus
5. Cache updated if applicable
6. Response returned

---

### Asynchronous Flow (WebSocket/Celery)

```
User Action → WebSocket Consumer → Orchestrator → Tool Decision → Tool Execution
                                    ↓
                              Entity Resolution
                                    ↓
                              Model Layer → Router
                                    ↓
                              Event Bus Publish
```

**Triggers:**
- WebSocket connection (api/consumers.py)
- Celery task queue (services/tasks.py)
- Background document processing

**Execution:**
1. Consumer receives message
2. Orchestrator plans execution
3. Entity resolver resolves references
4. Tool decision engine selects tools
5. Tools execute (parallel or sequential)
6. Results synthesized
7. Response streamed or queued
8. Events published

---

## Failure Strategies

### Layer 1 Failures (Critical)

**Django Server Failure:**
- **Detection**: Server crash, 500 errors
- **Fallback**: Restart via process manager (systemd/supervisor)
- **Impact**: Complete outage
- **Recovery**: Automatic restart, health check endpoint

**Event Bus Failure:**
- **Detection**: Event publish fails, subscriber error
- **Fallback**: Log event to file, continue execution
- **Impact**: No real-time updates, cached data stale
- **Recovery**: Restart event bus on next request

**Redis Cache Failure:**
- **Detection**: Cache get/set fails
- **Fallback**: Disable caching, use in-memory dict
- **Impact**: Slower responses, no user context
- **Recovery**: Reconnect to Redis, warm cache

**Service Layer Failure:**
- **Detection**: Service method raises exception
- **Fallback**: Return 500 error with details
- **Impact**: Feature unavailable
- **Recovery**: Fix service code, redeploy

---

### Layer 2 Failures (Degraded)

**Router Failure (All AI Providers Down):**
- **Detection**: ModelUnavailableError raised
- **Fallback**: Return "AI service unavailable" message
- **Impact**: No AI responses, manual task entry only
- **Recovery**: Check API keys, network connectivity

**Model Layer Failure:**
- **Detection**: call_model() fails
- **Fallback**: Use cached response if available, else error
- **Impact**: AI features unavailable
- **Recovery**: Restart router, check provider status

**Document Processing Failure:**
- **Detection**: process_document() raises exception
- **Fallback**: Mark document as "failed", log error
- **Impact**: Document not indexed, search unavailable
- **Recovery**: Retry via admin reindex endpoint

**Email Service Failure:**
- **Detection**: SMTP send fails
- **Fallback**: Log email to console, continue
- **Impact**: No email notifications
- **Recovery**: Check SMTP config, retry queue

**Celery Worker Failure:**
- **Detection**: Task not picked up, timeout
- **Fallback**: Execute task synchronously
- **Impact**: Slower responses
- **Recovery**: Restart Celery workers

---

### Layer 3 Failures (Graceful Degradation)

**Orchestrator Failure:**
- **Detection**: Orchestrator exception
- **Fallback**: Return direct service response without AI
- **Impact**: No multi-step reasoning
- **Recovery**: Restart orchestrator, check dependencies

**Entity Resolver Failure:**
- **Detection**: Resolution error
- **Fallback**: Ask user for clarification
- **Impact**: More user interaction required
- **Recovery**: Check conversation history format

**Tool Decision Engine Failure:**
- **Detection**: Decision error
- **Fallback**: Use default tool set for intent
- **Impact**: Suboptimal tool selection
- **Recovery**: Reload tool definitions

**MCP Tool Failure:**
- **Detection**: Tool execution error
- **Fallback**: Skip tool, continue with others
- **Impact**: Missing data in response
- **Recovery**: Check tool configuration

---

## Dependency Graph

```
Django Server (L1)
    ├─→ Event Bus (L1)
    │   └─→ Service Layer (L1)
    │       ├─→ AuthService
    │       ├─→ TaskService
    │       ├─→ DocumentService
    │       ├─→ ProfileService
    │       ├─→ ChatService
    │       ├─→ ConversationService
    │       └─→ MessageService
    │
    ├─→ Redis Cache (L1)
    │   └─→ Model Layer (L2)
    │       └─→ Router (L2)
    │           ├─→ Gemini Provider
    │           ├─→ Groq Provider
    │           └─→ OpenRouter Provider
    │
    ├─→ Document Processing (L2)
    │   └─→ Model Layer (L2)
    │
    ├─→ Email Service (L2)
    │   └─→ SMTP Server
    │
    └─→ Celery Workers (L2)
        └─→ Redis Broker

Orchestrator (L3)
    ├─→ Model Layer (L2)
    ├─→ Entity Resolver (L3)
    │   └─→ Conversation History
    ├─→ Tool Decision Engine (L3)
    │   └─→ MCP Tools (L3)
    └─→ Event Bus (L1)

WebSocket Consumers
    ├─→ Orchestrator (L3)
    └─→ Service Layer (L1)
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] PostgreSQL database created and migrated
- [ ] Redis server running
- [ ] Environment variables configured (.env)
- [ ] AI API keys set (Gemini, Groq, OpenRouter)
- [ ] SMTP configured for email
- [ ] Celery broker configured (Redis)
- [ ] Static files collected
- [ ] Media directory permissions set

### Core System Deployment

- [ ] Deploy Django application (Render/Heroku)
- [ ] Verify event bus subscriptions (check logs)
- [ ] Test Redis connection (cache test)
- [ ] Verify service layer imports (Django check)
- [ ] Run system health check: `/api/v1/health/`

### Supporting Services Deployment

- [ ] Test AI provider fallback chain
- [ ] Verify document processing pipeline
- [ ] Test email sending (verification flow)
- [ ] Start Celery workers (if using)
- [ ] Verify Celery beat (scheduled tasks)

### Agent System Deployment

- [ ] Test orchestrator with simple query
- [ ] Test entity resolution ("that document")
- [ ] Test tool decision engine
- [ ] Verify MCP tool registration
- [ ] Test WebSocket connection

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check event bus subscriptions
- [ ] Verify cache hit rates
- [ ] Test AI provider failover
- [ ] Load test API endpoints
- [ ] Verify rate limiting

---

## Configuration Reference

### Required Environment Variables

```bash
# Django
SECRET_KEY=[generated]
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://...

# AI Providers
GEMINI_API_KEY=...
GROQ_API_KEY=...
OPENROUTER_API_KEY=...

# Redis
REDIS_URL=redis://...

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Celery (optional)
CELERY_BROKER_URL=redis://...
```

### Optional Environment Variables

```bash
# Document Processing
MAX_UPLOAD_SIZE_MB=10
CHUNK_SIZE_CHARS=1500
MAX_CHUNKS_PER_DOC=20

# Rate Limits
GEMINI_TIMEOUT=15
GROQ_TIMEOUT=10
OPENROUTER_TIMEOUT=20
MAX_TOOL_ITERATIONS=6

# Frontend
FRONTEND_URL=https://your-frontend.com
```

---

## Monitoring

### Key Metrics

- **Event Bus**: Subscription count, publish rate, error rate
- **Cache**: Hit rate, memory usage, connection count
- **AI Providers**: Success rate per provider, fallback rate, latency
- **Orchestrator**: Reasoning chain length, tool usage, confidence scores
- **Services**: Request rate, error rate, response time

### Log Patterns

```
# Event Bus
Subscribed to event: task.created
Subscribed to event: document.uploaded

# Router
Model used: gemini/gemini-2.0-flash
Model used: groq/llama-3.1-8b-instant (fallback)
Gemini timed out → falling back to Groq

# Orchestrator
Execution plan: 3 tools, sequential
Tool used: get_tasks, cache hit
Confidence: 0.85, memory stored
```

### Health Checks

- `/api/v1/health/` - System health
- `/api/v1/admin/dashboard/` - Admin stats (requires admin)
- Redis: `redis-cli ping`
- Celery: `celery -A config inspect active`

---

## Rollback Procedure

### Immediate Rollback

1. Revert to previous git commit
2. Redeploy to production
3. Run migrations if needed
4. Restart services
5. Verify health check

### Partial Rollback

If only agents fail:
1. Disable agent features in settings
2. Keep core services running
3. Continue with manual task entry
4. Fix agent code
5. Redeploy agents only

---

## Troubleshooting

### Event Bus Not Subscribing

**Symptom**: No "Subscribed to event" logs
**Cause**: Event bus not initialized
**Fix**: Check core/events/__init__.py import, restart server

### Cache Not Working

**Symptom**: Cache miss on every request
**Cause**: Redis connection failed
**Fix**: Check REDIS_URL, verify Redis server running

### AI Providers All Failing

**Symptom**: "All AI providers failed" error
**Cause**: API keys missing or network issue
**Fix**: Verify API keys in .env, test network connectivity

### Orchestrator Not Responding

**Symptom**: Chat endpoint hangs
**Cause**: Tool decision engine stuck
**Fix**: Check MAX_TOOL_ITERATIONS, verify tool definitions

### WebSocket Not Connecting

**Symptom**: Connection refused
**Cause**: ASGI server not running
**Fix**: Deploy Daphne/ASGI server, check routing.py
