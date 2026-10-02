# AEIOU AI - Documentation Index

## Quick Links

| Document | Description |
|----------|-------------|
| [API Reference](API.md) | Complete API endpoint documentation |
| [Architecture](ARCHITECTURE.md) | System architecture & design decisions |
| [Runbooks](RUNBOOKS.md) | Operations procedures & incident response |
| [OpenAPI Schema](openapi_schema.json) | Machine-readable API spec (OpenAPI 3.0) |
| [Swagger UI](https://api.aeiou.ai/api/docs/) | Interactive API explorer |

## Project Status

### Completed Phases
- ✅ **Phase 0**: Stabilization (SSE timeout, pgvector, RAG wiring, summaries, refresh tokens, circuit breakers)
- ✅ **Phase 1**: Real RAG + Document Intelligence (citations, analysis, Q&A, reranking)
- ✅ **Phase 2**: Reliable Long-term Memory (summaries, embeddings, WorkspaceContext, memory API)
- ✅ **Phase 3**: Users/Roles/Permissions/Assignment (RBAC, collaborators, invitations, notifications)
- ✅ **Phase 4**: Documentation (API docs, runbooks, architecture) - **THIS PHASE**

### Test Status
- **88 tests passing** across all phases
- Backend: Python/Django REST Framework
- Frontend: Next.js/TypeScript (builds successfully, no lint errors)

## Key Features

### Core Capabilities
- **Task Management**: Full CRUD, subtasks, time tracking, collaborators, comments
- **Document Processing**: Upload, OCR, chunking, embeddings, semantic search
- **AI Chat**: Streaming responses, RAG with citations, conversation memory
- **Workspaces**: Multi-tenant with RBAC (owner/admin/member/viewer)
- **Real-time**: SSE for chat streaming, live task updates
- **Integrations**: Webhooks, Zapier, API tokens

### Technical Highlights
- **Vector Search**: pgvector with HNSW indexing
- **Authentication**: JWT with refresh token rotation
- **Async Processing**: Celery + Redis for document processing, embeddings
- **Caching**: Multi-layer (Redis, application-level)
- **Monitoring**: Structured logging, health checks, metrics

## Getting Started

### Local Development
```bash
# Clone and setup
git clone https://github.com/your-org/aeiou-ai.git
cd aeiou-ai

# Start services
docker-compose up -d

# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/aeoiu
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional
SENTRY_DSN=https://...
DATADOG_API_KEY=...
```

## API Quick Reference

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/tasks/
```

### Create Task
```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "New task", "workspace": "<workspace-id>"}'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "workspace=<workspace-id>"
```

### Chat (Streaming)
```bash
curl -N -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_id": "<id>"}' \
  http://localhost:8000/api/v1/conversations/<id>/stream/
```

## Deployment

### Staging (Railway)
- Automatic on push to `develop` branch
- URL: `https://staging-api.aeiou.ai`

### Production (AWS ECS)
- Manual approval required
- Tag release: `git tag v1.0.0 && git push origin v1.0.0`
- URL: `https://api.aeiou.ai`

## Monitoring

### Health Checks
- `GET /health/` - Liveness
- `GET /health/ready/` - Readiness (DB, Redis, pgvector)
- `GET /health/startup/` - Startup

### Key Metrics
- API latency (p50, p95, p99)
- Error rates
- Queue depths
- Database connections
- Cache hit rates

## Support

- **Documentation**: This directory
- **API Explorer**: `/api/docs/` (Swagger UI)
- **Issues**: GitHub Issues
- **On-call**: See RUNBOOKS.md for contacts

## License

Proprietary - All rights reserved.