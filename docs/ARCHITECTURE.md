# AEIOU AI - Architecture Documentation

## Overview

AEIOU AI is a business assistant application built with Django (backend) and Next.js (frontend). It provides task management, document processing, AI-powered chat, and comprehensive user management capabilities.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   Django API    │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 3000)   │    │   (Port 8000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Redis Cache   │              │
         │              │   (Port 6379)   │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Celery        │              │
         │              │   Background    │              │
         │              │   Tasks         │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   WebSocket     │              │
         │              │   (Channels)    │              │
         │              └─────────────────┘              │
```

## Technology Stack

### Backend (Django)
- **Framework**: Django 5.2.14 with Django REST Framework
- **Database**: PostgreSQL (required for all environments)
- **Caching**: Redis with django-redis
- **Authentication**: JWT with django-rest-framework-simplejwt
- **Background Tasks**: Celery with Redis broker
- **WebSocket**: Django Channels with Daphne ASGI server
- **File Storage**: Django-storages with S3 support
- **Documentation**: drf-spectacular (OpenAPI/Swagger)

### Frontend (Next.js)
- **Framework**: Next.js 16.2.6 with React 18.3.1
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4.0
- **UI Components**: Radix UI, shadcn/ui
- **State Management**: React hooks and context
- **HTTP Client**: Axios
- **Real-time**: WebSocket client

### Infrastructure & DevOps
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry for error tracking
- **Logging**: Structured logging with Django's logging framework
- **Performance**: Prometheus metrics
- **Static Files**: Whitenoise for production serving

## Core Components

### 1. Authentication & Authorization
- JWT-based authentication with refresh tokens
- Token blacklisting for secure logout
- Role-based permissions
- Rate limiting on authentication endpoints

### 2. Task Management System
- **Models**: Task, TaskTag, TaskComment, TaskActivity, TaskAttachment
- **Features**: 
  - CRUD operations with soft delete
  - Tagging and categorization
  - Activity logging
  - File attachments
  - AI-powered suggestions
  - Subtask management
- **Real-time**: WebSocket updates for task changes

### 3. Document Processing
- **Supported Formats**: PDF, DOCX, images
- **Features**: 
  - File upload and storage
  - Text extraction
  - AI-powered analysis
  - Version control
- **Storage**: S3 with local fallback

### 4. AI Integration
- **Providers**: Google Gemini, Groq, OpenRouter
- **Features**:
  - Chat interface with conversation memory
  - Document analysis
  - Task suggestions
  - Smart task completion

### 5. Event System
- **Event Bus**: Custom implementation for decoupled communication
- **Event Types**: task.created, task.updated, document.uploaded, user.actions
- **Handlers**: Audit logging, notifications, cache invalidation

### 6. Caching Strategy
- **Levels**: Application-level (Redis), Database-level
- **Cache Keys**: User-specific, task-specific, API responses
- **Invalidation**: Event-driven cache invalidation
- **TTL**: Configurable per cache type

## Database Schema

### Core Models

#### User Management
```python
User (Django auth)
├── BusinessProfile
│   ├── company_name
│   ├── industry
│   └── settings
└── APIToken
    ├── token
    ├── expires_at
    └── last_used
```

#### Task System
```python
Task
├── TaskTag
├── TaskComment
├── TaskActivity (audit trail)
├── TaskAttachment
├── TaskAISuggestion
└── TaskSubtask
```

#### Document System
```python
Document
├── DocumentVersion
└── DocumentAnalysis
```

#### Chat System
```python
Conversation
├── Message
└── ConversationMemory
```

## API Design

### RESTful API Structure
```
/api/v1/
├── auth/
│   ├── login/
│   ├── logout/
│   ├── refresh/
│   └── register/
├── tasks/
│   ├── ├── (list/create)
│   ├── <uuid>/
│   │   ├── (get/update/delete)
│   │   ├── comments/
│   │   ├── attachments/
│   │   └── activity/
│   └── tags/
├── documents/
│   ├── (list/upload)
│   └── <uuid>/
├── profiles/
│   ├── me/
│   └── settings/
├── chat/
│   ├── conversations/
│   └── messages/
└── admin/
    ├── users/
    └── analytics/
```

### Authentication Flow
1. User credentials → POST /api/v1/auth/login/
2. JWT access token + refresh token returned
3. Access token used in Authorization header
4. Refresh token used to get new access token
5. Logout → POST /api/v1/auth/logout/ (token blacklisting)

## Security Architecture

### 1. Authentication Security
- JWT with RS256 signing
- Short access token lifetime (15 minutes)
- Refresh token rotation
- Token blacklisting on logout

### 2. API Security
- Rate limiting per endpoint
- CORS configuration
- Input validation and sanitization
- SQL injection prevention (Django ORM)
- XSS protection (bleach for HTML)

### 3. Data Security
- Encrypted data transmission (HTTPS)
- Sensitive data encryption at rest
- Secure file upload handling
- Audit logging for all user actions

### 4. Infrastructure Security
- Environment variable management
- Secret rotation policies
- Network security groups
- Regular security updates

## Performance Optimization

### 1. Database Optimization
- Database indexing on foreign keys and frequently queried fields
- Query optimization with select_related and prefetch_related
- Database connection pooling
- Read replicas for scaling

### 2. Caching Strategy
- Redis for application-level caching
- Database query caching
- Static asset caching
- CDN integration for static files

### 3. API Performance
- Pagination for large datasets
- Response compression
- Efficient serialization
- Background task processing

### 4. Frontend Optimization
- Code splitting and lazy loading
- Image optimization
- Bundle size optimization
- Service worker for offline support

## Monitoring & Observability

### 1. Error Tracking
- Sentry integration for error monitoring
- Custom error logging
- Performance monitoring
- User context in errors

### 2. Metrics Collection
- Prometheus metrics for application performance
- Database performance metrics
- Cache hit rates
- API response times

### 3. Logging Strategy
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request ID tracking
- Sensitive data filtering

## Deployment Architecture

### Development Environment
```
Docker Compose:
├── Django app (port 8000)
├── PostgreSQL (port 5432)
├── Redis (port 6379)
├── Celery worker
├── Celery beat (scheduler)
└── Next.js dev server (port 3000)
```

### Production Environment
```
Kubernetes/Cloud:
├── Load Balancer
├── Django app (multiple replicas)
├── PostgreSQL (managed database)
├── Redis (managed cache)
├── Celery workers (auto-scaling)
├── Static files (CDN)
└── Media files (S3)
```

## Development Workflow

### 1. Local Development
```bash
# Backend
cd /backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd /frontend
npm install
npm run dev
```

### 2. Testing Strategy
- **Backend**: pytest with 100% test coverage
- **Frontend**: Jest + React Testing Library
- **Integration**: API testing with pytest-django
- **E2E**: Playwright for critical user flows

### 3. Code Quality
- **Backend**: flake8, black, isort
- **Frontend**: ESLint, Prettier
- **Type Checking**: mypy (backend), TypeScript (frontend)
- **Security**: bandit (backend), npm audit (frontend)

## Scaling Considerations

### 1. Horizontal Scaling
- Stateless application design
- Database connection pooling
- Load balancer configuration
- Auto-scaling policies

### 2. Database Scaling
- Read replicas for read-heavy workloads
- Database sharding strategy
- Connection pooling optimization
- Query performance monitoring

### 3. Cache Scaling
- Redis clustering
- Cache warming strategies
- Cache invalidation optimization
- Multi-level caching

### 4. Frontend Scaling
- CDN deployment
- Edge computing
- Progressive loading
- Offline capabilities

## Future Enhancements

### 1. Microservices Migration
- Service decomposition strategy
- Inter-service communication
- Distributed tracing
- Service mesh implementation

### 2. Advanced AI Features
- Custom model training
- Real-time collaboration
- Advanced analytics
- Predictive capabilities

### 3. Mobile Application
- React Native development
- Offline synchronization
- Push notifications
- Native integrations

### 4. Enterprise Features
- Multi-tenancy
- Advanced permissions
- SSO integration
- Compliance features (GDPR, SOC2)

---

This architecture documentation provides a comprehensive overview of the AEIOU AI system. For specific implementation details, refer to the individual component documentation and code comments.
