# AEIOU AI - API Documentation

## Overview

The AEIOU AI API is a RESTful API built with Django REST Framework, providing comprehensive endpoints for task management, document processing, AI-powered chat, workspace collaboration, and more.

**Base URL**: `https://api.aeiou.ai/api/v1/`
**Staging**: `https://staging-api.aeiou.ai/api/v1/`
**Local**: `http://localhost:8000/api/v1/`

## Authentication

All API endpoints (except auth) require JWT Bearer token authentication.

### Get Access Token
```bash
curl -X POST https://api.aeiou.ai/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user",
    "is_staff": false
  }
}
```

### Use Token
```bash
curl -X GET https://api.aeiou.ai/api/v1/tasks/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Refresh Token
```bash
curl -X POST https://api.aeiou.ai/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJhbGciOiJIUzI1NiIs..."}'
```

## OpenAPI Schema

The complete OpenAPI 3.0 specification is available at:
- **Interactive**: `https://api.aeiou.ai/api/docs/` (Swagger UI)
- **Raw JSON**: `https://api.aeiou.ai/api/schema/`
- **Raw YAML**: `https://api.aeiou.ai/api/schema/?format=yaml`
- **Local file**: `docs/openapi_schema.json`

## Endpoint Reference

### Authentication (`/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | User login |
| POST | `/auth/register/` | User registration |
| POST | `/auth/token/refresh/` | Refresh access token |
| POST | `/auth/logout/` | Logout (revoke refresh token) |
| POST | `/auth/verify-email/` | Verify email with token |
| POST | `/auth/resend-verification/` | Resend verification email |
| POST | `/auth/forgot-password/` | Request password reset |
| POST | `/auth/verify-reset-code/` | Verify reset code |
| POST | `/auth/reset-password/` | Reset password |

### Users (`/users/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me/` | Current user profile |
| PATCH | `/users/me/` | Update profile |
| GET | `/users/me/sessions/` | List active sessions |
| DELETE | `/users/me/sessions/{id}/` | Revoke session |
| DELETE | `/users/me/sessions/` | Revoke all other sessions |
| GET | `/users/me/api-tokens/` | List API tokens |
| POST | `/users/me/api-tokens/` | Create API token |
| DELETE | `/users/me/api-tokens/{id}/` | Revoke API token |

### Workspaces (`/workspaces/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/` | List workspaces |
| POST | `/workspaces/` | Create workspace |
| GET | `/workspaces/{id}/` | Get workspace |
| PATCH | `/workspaces/{id}/` | Update workspace |
| DELETE | `/workspaces/{id}/` | Archive workspace |
| GET | `/workspaces/{id}/context/` | Get workspace context |
| PATCH | `/workspaces/{id}/context/` | Update business context |
| GET | `/workspaces/{id}/preferences/` | Get preferences |
| PATCH | `/workspaces/{id}/preferences/` | Update preferences |

### Workspace Members (`/workspaces/{id}/members/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/{id}/members/` | List members |
| POST | `/workspaces/{id}/members/` | Invite member |
| PATCH | `/workspaces/{id}/members/{user_id}/` | Update member role |
| DELETE | `/workspaces/{id}/members/{user_id}/` | Remove member |

### Workspace Invitations (`/workspaces/{id}/invitations/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/{id}/invitations/` | List invitations |
| POST | `/workspaces/{id}/invitations/` | Create invitation |
| DELETE | `/workspaces/{id}/invitations/{id}/` | Revoke invitation |
| POST | `/invitations/accept/` | Accept invitation (public) |

### Tasks (`/tasks/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/` | List tasks (with filters) |
| POST | `/tasks/` | Create task |
| GET | `/tasks/{id}/` | Get task details |
| PATCH | `/tasks/{id}/` | Update task |
| DELETE | `/tasks/{id}/` | Delete task |
| POST | `/tasks/{id}/complete/` | Mark complete |
| POST | `/tasks/{id}/reopen/` | Reopen task |
| GET | `/tasks/{id}/activities/` | List activities |
| GET | `/tasks/stats/` | Task statistics |
| GET | `/tasks/dashboard/` | Dashboard data |

### Task Collaborators (`/tasks/{id}/collaborators/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{id}/collaborators/` | List collaborators |
| POST | `/tasks/{id}/collaborators/` | Add collaborator |
| DELETE | `/tasks/{id}/collaborators/{user_id}/` | Remove collaborator |

### Task Comments (`/tasks/{id}/comments/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{id}/comments/` | List comments |
| POST | `/tasks/{id}/comments/` | Add comment |
| PATCH | `/tasks/{id}/comments/{comment_id}/` | Edit comment |
| DELETE | `/tasks/{id}/comments/{comment_id}/` | Delete comment |
| POST | `/tasks/{id}/comments/{comment_id}/reply/` | Reply to comment |

### Task Subtasks (`/tasks/{id}/subtasks/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{id}/subtasks/` | List subtasks |
| POST | `/tasks/{id}/subtasks/` | Add subtask |
| PATCH | `/tasks/{id}/subtasks/{subtask_id}/` | Update subtask |
| DELETE | `/tasks/{id}/subtasks/{subtask_id}/` | Delete subtask |

### Task Time Entries (`/tasks/{id}/time-entries/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{id}/time-entries/` | List time entries |
| POST | `/tasks/{id}/time-entries/` | Add manual time |
| POST | `/tasks/{id}/timer/start/` | Start timer |
| POST | `/tasks/{id}/timer/stop/` | Stop timer |
| GET | `/tasks/{id}/timer/active/` | Get active timer |
| DELETE | `/tasks/{id}/time-entries/{entry_id}/` | Delete time entry |

### Chat / Conversations (`/conversations/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/conversations/` | List conversations |
| POST | `/conversations/` | Create conversation |
| GET | `/conversations/{id}/` | Get conversation |
| DELETE | `/conversations/{id}/` | Delete conversation |
| POST | `/conversations/{id}/messages/` | Send message (non-streaming) |
| GET | `/conversations/{id}/stream/` | Stream chat (SSE) |
| POST | `/conversations/{id}/export/` | Export conversation |

### Documents (`/documents/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/` | List documents |
| POST | `/documents/` | Upload document |
| GET | `/documents/{id}/` | Get document |
| DELETE | `/documents/{id}/` | Delete document |
| GET | `/documents/{id}/download/` | Download file |
| GET | `/documents/{id}/status/` | Processing status |
| POST | `/documents/{id}/reprocess/` | Reprocess document |
| GET | `/documents/{id}/summary/` | Get summary |
| GET | `/documents/status/summary/` | Status summary |

### Document Analysis (`/documents/{id}/analysis/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/{id}/analysis/` | Analyze document |
| GET | `/documents/{id}/analysis/` | Get analysis |
| POST | `/documents/{id}/analysis/extract-tasks/` | Extract tasks |
| GET | `/documents/{id}/analysis/insights/` | Get insights |

### Document Versions (`/documents/{id}/versions/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/versions/` | List versions |
| POST | `/documents/{id}/versions/` | Create version |
| GET | `/documents/{id}/versions/{version_id}/` | Get version |
| GET | `/documents/{id}/versions/{version_id}/diff/` | Compare versions |

### Semantic Search (`/search/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search/semantic/` | Semantic search |
| POST | `/search/conversational/` | Conversational retrieval |
| POST | `/search/generate-embeddings/` | Generate embeddings |

### Memory (`/memories/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/memories/` | List memories |
| POST | `/memories/` | Create memory |
| GET | `/memories/{id}/` | Get memory |
| PATCH | `/memories/{id}/` | Update memory |
| DELETE | `/memories/{id}/` | Delete memory |
| POST | `/memories/regenerate-embeddings/` | Regenerate embeddings |

### Notifications (`/notifications/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | List notifications |
| PATCH | `/notifications/{id}/read/` | Mark as read |
| POST | `/notifications/read-all/` | Mark all as read |
| GET | `/notifications/preferences/` | Get preferences |
| PATCH | `/notifications/preferences/` | Update preferences |
| GET | `/notifications/unread-count/` | Get unread count |

### Webhooks (`/webhooks/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhooks/` | List webhooks |
| POST | `/webhooks/` | Create webhook |
| GET | `/webhooks/{id}/` | Get webhook |
| PATCH | `/webhooks/{id}/` | Update webhook |
| DELETE | `/webhooks/{id}/` | Delete webhook |
| POST | `/webhooks/{id}/test/` | Test webhook |
| POST | `/webhooks/{id}/regenerate-secret/` | Regenerate secret |
| GET | `/webhooks/{id}/deliveries/` | List deliveries |
| GET | `/webhooks/events/` | Available events |

### Analytics (`/analytics/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/dashboard/` | Admin dashboard |
| GET | `/analytics/workspace/{id}/` | Workspace analytics |
| GET | `/analytics/engagement/` | User engagement |
| GET | `/analytics/ai-usage/` | AI usage stats |
| POST | `/analytics/export/` | Request export |
| GET | `/analytics/export/{id}/` | Export status |
| GET | `/analytics/retention/` | Retention report |

### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/integrations/status/` | Integration status |
| GET | `/integrations/zapier/triggers/` | Zapier triggers |
| GET | `/integrations/zapier/actions/` | Zapier actions |
| GET | `/integrations/zapier/sample-data/` | Zapier sample data |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Health check |
| GET | `/health/ready/` | Readiness check |
| GET | `/health/startup/` | Startup check |
| GET | `/ai/health/` | AI service health |
| GET | `/actions/smart/` | Natural language commands |
| POST | `/admin/broadcast/` | Admin broadcast |
| GET | `/admin/dashboard/` | Admin dashboard |
| GET | `/tags/` | List tags |
| POST | `/tags/` | Create tag |
| GET | `/tasks/by-tag/` | Tasks by tag |

## Query Parameters

### Pagination
```
?page=1&page_size=20
```
Response includes: `count`, `next`, `previous`, `results`

### Filtering
```
?status=todo&assignee=me&priority=high
?workspace=uuid&created_after=2024-01-01
```

### Sorting
```
?ordering=-created_at,title
?ordering=due_date,-priority
```

### Search
```
?search=query text
```

## Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.aeiou.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid input data",
  "instance": "/api/v1/tasks/",
  "errors": {
    "title": ["This field is required."],
    "due_date": ["Invalid date format."]
  }
}
```

Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request (validation)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Unprocessable Entity
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limits

| Tier | Requests/minute | Burst |
|------|-----------------|-------|
| Free | 60 | 10 |
| Pro | 300 | 50 |
| Enterprise | 1000 | 200 |

Headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1704067200
```

## Webhooks

### Configuration
- Set target URL in webhook configuration
- Select events to subscribe to
- Secret used for signature verification

### Event Payload
```json
{
  "event": "task.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "workspace_id": "uuid",
  "data": {
    "id": "uuid",
    "title": "New task",
    "status": "todo"
  }
}
```

### Signature Verification
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Available Events
- `task.created`, `task.updated`, `task.deleted`, `task.completed`
- `comment.created`, `comment.updated`, `comment.deleted`
- `document.uploaded`, `document.processed`, `document.failed`
- `conversation.created`, `message.created`
- `member.invited`, `member.joined`, `member.removed`
- `workspace.updated`, `workspace.archived`

## SDKs & Client Libraries

### Python
```bash
pip install aeiou-ai-client
```

```python
from aeiou_ai import Client

client = Client(api_key="your-api-key")
tasks = client.tasks.list(workspace_id="uuid")
```

### JavaScript/TypeScript
```bash
npm install @aeiou/ai-client
```

```typescript
import { AEIOUClient } from '@aeiou/ai-client';

const client = new AEIOUClient({ apiKey: 'your-api-key' });
const tasks = await client.tasks.list({ workspaceId: 'uuid' });
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Task management, documents, chat, workspaces
- RBAC permissions
- Semantic search & RAG
- Webhooks & integrations

### v1.1.0 (2024-02-01)
- Task time tracking
- Document versioning
- Conversation summaries
- Long-term memory
- Admin analytics

---

For the complete OpenAPI specification, see:
- **Live**: `https://api.aeiou.ai/api/schema/`
- **File**: `docs/openapi_schema.json`
- **Interactive**: `https://api.aeiou.ai/api/docs/`