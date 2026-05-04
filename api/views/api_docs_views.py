"""API Documentation Views - OpenAPI/Swagger spec and examples."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import json


OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "AEIOU AI API",
        "description": "REST API for AEIOU AI - AI-powered task management and document analysis",
        "version": "1.0.0",
        "contact": {
            "name": "AEIOU AI Support",
            "email": "api@aeiou.ai"
        }
    },
    "servers": [
        {
            "url": "https://api.aeiou.ai/v1",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Local development"
        }
    ],
    "security": [
        {"BearerAuth": []},
        {"ApiTokenAuth": []}
    ],
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "ApiTokenAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Token"
            }
        },
        "schemas": {
            "Task": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "title": {"type": "string", "example": "Complete project documentation"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_date": {"type": "string", "format": "date"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "title", "status", "priority"]
            },
            "Document": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "title": {"type": "string"},
                    "file_type": {"type": "string", "example": "pdf"},
                    "file_size": {"type": "integer", "description": "Size in bytes"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "ai_summary": {"type": "string"}
                }
            },
            "Webhook": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "name": {"type": "string", "example": "Zapier Production"},
                    "url": {"type": "string", "format": "uri"},
                    "events": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["task.created", "task.completed"]
                    },
                    "is_active": {"type": "boolean"},
                    "secret": {"type": "string", "description": "HMAC signing secret"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "detail": {"type": "string"}
                }
            }
        }
    },
    "paths": {
        "/auth/login/": {
            "post": {
                "summary": "User login",
                "tags": ["Authentication"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string", "format": "password"}
                                },
                                "required": ["email", "password"]
                            },
                            "example": {
                                "email": "user@example.com",
                                "password": "your-password"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "example": {
                                    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                                    "user": {"id": 1, "email": "user@example.com"}
                                }
                            }
                        }
                    },
                    "401": {"description": "Invalid credentials"}
                }
            }
        },
        "/tasks/": {
            "get": {
                "summary": "List all tasks",
                "tags": ["Tasks"],
                "parameters": [
                    {"name": "status", "in": "query", "schema": {"type": "string"}},
                    {"name": "priority", "in": "query", "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}}
                ],
                "responses": {
                    "200": {
                        "description": "List of tasks",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tasks": {"type": "array", "items": {"$ref": "#/components/schemas/Task"}},
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a new task",
                "tags": ["Tasks"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "status": {"type": "string", "enum": ["todo", "in_progress", "done"], "default": "todo"},
                                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                                    "due_date": {"type": "string", "format": "date"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                    "assigned_to": {"type": "integer"}
                                },
                                "required": ["title"]
                            },
                            "example": {
                                "title": "Review quarterly report",
                                "description": "Check all numbers before submission",
                                "priority": "high",
                                "due_date": "2024-12-31",
                                "tags": ["finance", "urgent"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Task created", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}}
                }
            }
        },
        "/tasks/{task_id}/": {
            "get": {
                "summary": "Get task details",
                "tags": ["Tasks"],
                "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Task details", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}},
                    "404": {"description": "Task not found"}
                }
            },
            "put": {
                "summary": "Update task",
                "tags": ["Tasks"],
                "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Task"}
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Task updated"}
                }
            },
            "delete": {
                "summary": "Delete task",
                "tags": ["Tasks"],
                "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Task deleted"}
                }
            }
        },
        "/webhooks/": {
            "get": {
                "summary": "List webhooks",
                "tags": ["Webhooks"],
                "responses": {
                    "200": {
                        "description": "List of webhooks",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "webhooks": {"type": "array", "items": {"$ref": "#/components/schemas/Webhook"}}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create webhook",
                "tags": ["Webhooks"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "example": "Zapier Production"},
                                    "url": {"type": "string", "format": "uri"},
                                    "events": {"type": "array", "items": {"type": "string"}},
                                    "headers": {"type": "object"}
                                },
                                "required": ["name", "url", "events"]
                            },
                            "example": {
                                "name": "Zapier Production",
                                "url": "https://hooks.zapier.com/hooks/catch/...",
                                "events": ["task.created", "task.completed"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Webhook created", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Webhook"}}}}
                }
            }
        },
        "/documents/": {
            "get": {
                "summary": "List documents",
                "tags": ["Documents"],
                "responses": {
                    "200": {"description": "List of documents", "content": {"application/json": {"schema": {"type": "object", "properties": {"documents": {"type": "array", "items": {"$ref": "#/components/schemas/Document"}}}}}}}
                }
            },
            "post": {
                "summary": "Upload document",
                "tags": ["Documents"],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "title": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Document uploaded"}
                }
            }
        },
        "/ai/chat/": {
            "post": {
                "summary": "Send message to AI",
                "tags": ["AI"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string", "example": "What are my high priority tasks?"},
                                    "conversation_id": {"type": "string", "format": "uuid"},
                                    "context": {"type": "object"}
                                },
                                "required": ["message"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "AI response",
                        "content": {
                            "application/json": {
                                "example": {
                                    "response": "You have 3 high priority tasks...",
                                    "suggested_tasks": [{"title": "Review report", "priority": "high"}],
                                    "conversation_id": "uuid-here"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/ai/generate-tasks/": {
            "post": {
                "summary": "Generate tasks from text using AI",
                "tags": ["AI"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "example": "We need to review the Q4 report and schedule a team meeting"},
                                    "accept_all": {"type": "boolean", "default": False}
                                },
                                "required": ["text"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Generated tasks",
                        "content": {
                            "application/json": {
                                "example": {
                                    "suggestions": [
                                        {"title": "Review Q4 report", "priority": "high", "reason": "Extracted from text"},
                                        {"title": "Schedule team meeting", "priority": "medium", "reason": "Extracted from text"}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "tags": [
        {"name": "Authentication", "description": "User login and token management"},
        {"name": "Tasks", "description": "Task CRUD operations"},
        {"name": "Documents", "description": "Document upload and management"},
        {"name": "Webhooks", "description": "Event subscriptions"},
        {"name": "AI", "description": "AI-powered features"}
    ]
}


@api_view(["GET"])
@permission_classes([AllowAny])
def get_openapi_spec(request):
    """Return OpenAPI 3.0 specification."""
    return Response(OPENAPI_SPEC)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_documentation(request):
    """HTML documentation page (simplified JSON for now)."""
    return Response({
        "api": {
            "version": "1.0.0",
            "base_url": "/api/v1",
            "authentication": {
                "methods": [
                    "Bearer Token (JWT) - use Authorization: Bearer <token>",
                    "API Token - use X-API-Token: <token>"
                ]
            },
            "endpoints": {
                "tasks": {
                    "description": "Task management",
                    "endpoints": [
                        {"method": "GET", "path": "/tasks/", "description": "List tasks"},
                        {"method": "POST", "path": "/tasks/", "description": "Create task"},
                        {"method": "GET", "path": "/tasks/{id}/", "description": "Get task"},
                        {"method": "PUT", "path": "/tasks/{id}/", "description": "Update task"},
                        {"method": "DELETE", "path": "/tasks/{id}/", "description": "Delete task"},
                    ]
                },
                "documents": {
                    "description": "Document management",
                    "endpoints": [
                        {"method": "GET", "path": "/documents/", "description": "List documents"},
                        {"method": "POST", "path": "/documents/", "description": "Upload document"},
                    ]
                },
                "webhooks": {
                    "description": "Event subscriptions",
                    "endpoints": [
                        {"method": "GET", "path": "/webhooks/", "description": "List webhooks"},
                        {"method": "POST", "path": "/webhooks/create/", "description": "Create webhook"},
                        {"method": "GET", "path": "/webhooks/{id}/deliveries/", "description": "View delivery log"},
                    ]
                },
                "integrations": {
                    "description": "Third-party integrations",
                    "endpoints": [
                        {"method": "GET", "path": "/integrations/status/", "description": "List available integrations"},
                        {"method": "GET", "path": "/integrations/zapier/triggers/", "description": "Zapier triggers"},
                        {"method": "GET", "path": "/integrations/zapier/actions/", "description": "Zapier actions"},
                    ]
                }
            },
            "rate_limits": {
                "authenticated": "1000 requests/hour",
                "api_tokens": "Configurable per token"
            },
            "webhooks": {
                "events": [
                    "task.created",
                    "task.updated",
                    "task.completed",
                    "task.deleted",
                    "document.created",
                    "document.updated",
                    "comment.created"
                ],
                "signature_header": "X-Webhook-Signature",
                "retry_policy": "3 attempts with exponential backoff"
            },
            "openapi_url": "/api/v1/docs/openapi.json"
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_api_examples(request):
    """Return code examples for common integrations."""
    return Response({
        "examples": {
            "javascript_fetch": {
                "description": "Using fetch() to create a task",
                "code": """const response = await fetch('https://api.aeiou.ai/v1/tasks/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My new task',
    priority: 'high',
    due_date: '2024-12-31'
  })
});
const task = await response.json();"""
            },
            "python_requests": {
                "description": "Using Python requests to list tasks",
                "code": """import requests

response = requests.get(
    'https://api.aeiou.ai/v1/tasks/',
    headers={'Authorization': 'Bearer YOUR_JWT_TOKEN'}
)
tasks = response.json()['tasks']"""
            },
            "curl": {
                "description": "Using curl to upload a document",
                "code": """curl -X POST https://api.aeiou.ai/v1/documents/ \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -F "file=@report.pdf" \\
  -F "title=Quarterly Report"
"""
            },
            "webhook_verification": {
                "description": "Verify webhook signature",
                "code": """import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)"""
            },
            "zapier_setup": {
                "description": "Setting up Zapier integration",
                "steps": [
                    "1. Create API token at /api/v1/tokens/create/",
                    "2. In Zapier, choose 'Webhooks by Zapier' as trigger",
                    "3. Set webhook URL to your endpoint",
                    "4. Use X-API-Token header for authentication",
                    "5. Select events to subscribe to"
                ]
            }
        }
    })
