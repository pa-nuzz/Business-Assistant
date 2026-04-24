# AEIOU AI - Frontend Routes Documentation

## App Router Structure

### Public Routes (No Auth Required)
| Route | File | Description |
|-------|------|-------------|
| `/` | `app/page.tsx` | Landing page / Home |
| `/login` | `app/login/page.tsx` | User login |
| `/register` | `app/register/page.tsx` | User registration |
| `/forgot-password` | `app/forgot-password/page.tsx` | Password reset request |
| `/reset-password` | `app/reset-password/page.tsx` | Password reset confirmation |
| `/verify-email` | `app/verify-email/page.tsx` | Email verification |

### Protected Routes (Auth Required)
| Route | File | Description |
|-------|------|-------------|
| `/chat` | `app/chat/page.tsx` | AI chat interface |
| `/documents` | `app/documents/page.tsx` | Document management |
| `/documents/[id]` | `app/documents/[id]/page.tsx` | Document detail view |
| `/tasks` | `app/tasks/page.tsx` | Task management (Kanban) |
| `/dashboard` | `app/dashboard/page.tsx` | Business analytics |
| `/settings` | `app/settings/page.tsx` | User settings & profile |

### API Routes
All API calls go to Django backend at `/api/v1/*`.

## Route Guards

- **Public routes**: Accessible without authentication
- **Protected routes**: Require valid JWT access token
- **Admin routes**: Require `is_staff` permission (handled by backend)

## Navigation Structure

```
Sidebar Navigation:
├── Chat (/chat)
├── Documents (/documents)
├── Tasks (/tasks)
├── Dashboard (/dashboard)
└── Settings (/settings)
```

## Component Organization

- **Page components**: `app/*/page.tsx` - Route entry points
- **Layout components**: `app/layout.tsx`, `components/layout/*`
- **Feature components**: `components/*` - Reusable UI components
- **Hooks**: `hooks/*` - Custom React hooks

## Code Splitting

Heavy components use dynamic imports:
- Document viewer
- Chart components
- Rich text editor
