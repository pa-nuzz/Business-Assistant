# API Reference

How to talk to the backend.

## Base URL

```
Production: https://api.yourdomain.com/api/v1/
Local: http://localhost:8000/api/v1/
```

## Authentication

Most endpoints need a JWT token. Pass it as a Bearer token in the Authorization header.

### Get Token
```bash
POST /auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Use Token
```bash
Authorization: Bearer <access_token>
```

### Refresh Token
```bash
POST /auth/refresh/
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}
```

---

## Tasks

### List Tasks
```bash
GET /tasks/?status=todo&priority=high&limit=20&offset=0
```

**Response:**
```json
{
  "count": 100,
  "next": "/api/v1/tasks/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Task name",
      "description": "Task description",
      "status": "todo|in_progress|done",
      "priority": "low|medium|high|urgent",
      "due_date": "2025-12-31",
      "assigned_to": { "id": "uuid", "name": "John" },
      "workspace": { "id": "uuid", "name": "Team A" },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Create Task
```bash
POST /tasks/create/
Content-Type: application/json

{
  "title": "New task",
  "description": "Task details",
  "status": "todo",
  "priority": "high",
  "due_date": "2025-12-31",
  "assigned_to": "user-uuid",
  "workspace": "workspace-uuid",
  "tags": ["tag1", "tag2"]
}
```

### Update Task
```bash
PUT /tasks/{task_id}/update/
PATCH /tasks/{task_id}/update/
```

### Delete Task
```bash
DELETE /tasks/{task_id}/delete/
```

### Complete/Reopen Task
```bash
POST /tasks/{task_id}/complete/
POST /tasks/{task_id}/reopen/
```

---

## Documents

### List Documents
```bash
GET /documents/?search=query&semantic=true&limit=20
```

### Upload Document
```bash
POST /documents/upload/
Content-Type: multipart/form-data

file: <binary>
name: "Document name"
workspace: "workspace-uuid"
```

### Get Document
```bash
GET /documents/{doc_id}/
```

### Semantic Search
```bash
POST /documents/search/
Content-Type: application/json

{
  "query": "search query",
  "filters": {
    "document_type": "pdf",
    "date_from": "2025-01-01"
  },
  "limit": 10
}
```

### Chat with Document
```bash
POST /documents/{doc_id}/chat/
Content-Type: application/json

{
  "message": "What does this document say about...?",
  "conversation_id": "uuid (optional)"
}
```

---

## AI Chat

### Send Message
```bash
POST /ai/chat/
Content-Type: application/json

{
  "message": "Generate tasks from: Meeting notes...",
  "context": "task_generation|document_analysis|general",
  "conversation_id": "uuid (optional)"
}
```

### Generate Tasks from Text
```bash
POST /ai/generate-tasks/
Content-Type: application/json

{
  "text": "Meeting notes...",
  "workspace_id": "uuid"
}
```

### Get AI Suggestions
```bash
GET /ai/suggestions/
```

---

## Workspaces

### List Workspaces
```bash
GET /workspaces/
```

### Create Workspace
```bash
POST /workspaces/create/
Content-Type: application/json

{
  "name": "My Team",
  "description": "Team workspace"
}
```

### Invite Member
```bash
POST /workspaces/{workspace_id}/invite/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "role": "member|admin"
}
```

### Update Member Role
```bash
PUT /workspaces/{workspace_id}/members/{member_id}/role/
Content-Type: application/json

{
  "role": "admin|member|viewer"
}
```

---

## Notifications

### Get Notifications
```bash
GET /notifications/?unread_only=true
```

### Mark Read
```bash
POST /notifications/{id}/read/
POST /notifications/mark-all-read/
```

---

## Analytics

### User Engagement
```bash
GET /analytics/engagement/?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "total_actions": 150,
  "active_days": 20,
  "engagement_score": 85.5,
  "feature_breakdown": [
    {"feature": "tasks", "count": 80},
    {"feature": "chat", "count": 40},
    {"feature": "documents", "count": 30}
  ]
}
```

### AI Usage
```bash
GET /analytics/ai-usage/?days=30
```

### Workspace Analytics
```bash
GET /analytics/workspaces/{workspace_id}/?days=30
```

---

## Webhooks

### Create Webhook
```bash
POST /webhooks/create/
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["task.created", "task.updated"],
  "secret": "your-secret"
}
```

### List Webhooks
```bash
GET /webhooks/
```

### Test Webhook
```bash
POST /webhooks/{webhook_id}/test/
```

---

## API Tokens (Zapier/Make)

### Create Token
```bash
POST /tokens/
Content-Type: application/json

{
  "name": "Zapier Production"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Zapier Production",
  "token": "aep_live_xxxxxxxxxxxxx",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### List Tokens
```bash
GET /tokens/
```

### Revoke Token
```bash
DELETE /tokens/{token_id}/revoke/
```

---

## Zapier Integration

### Triggers (Zapier)
```bash
GET /integrations/zapier/triggers/
```

Returns available triggers:
- `task.created`
- `task.completed`
- `document.uploaded`

### Actions (Zapier)
```bash
GET /integrations/zapier/actions/
```

Returns available actions:
- `create_task`
- `upload_document`

### Sample Data
```bash
GET /integrations/zapier/samples/{trigger_key}/
```

---

## Async Operations

### Process Document Async
```bash
POST /async/process-document/
Content-Type: application/json

{
  "document_id": "uuid"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "estimated_time": "30s"
}
```

### Check Job Status
```bash
GET /async/jobs/{job_id}/status/
```

**Response:**
```json
{
  "id": "uuid",
  "status": "pending|processing|completed|failed",
  "progress": 75,
  "result": {...},
  "error": null
}
```

---

## Errors

| Code | What it means |
|------|---------------|
| 400 | Bad request - check your input |
| 401 | Not authenticated - missing or bad token |
| 403 | No permission to do this |
| 404 | Resource not found |
| 429 | Rate limited - slow down |
| 500 | Server error - something broke |

Error response format:
```json
{
  "error": "What went wrong",
  "code": "error_code",
  "details": {...}
}
```

## Rate Limits

- Normal endpoints: 100 requests/minute
- AI endpoints: 20 requests/minute (they're expensive)
- Webhooks: 1000/hour

## Pagination

List endpoints return paginated results. Use `limit` and `offset` query params.

- `limit`: How many items (default 20, max 100)
- `offset`: Skip this many items

The response includes `count`, `next`, `previous`, and `results`.
