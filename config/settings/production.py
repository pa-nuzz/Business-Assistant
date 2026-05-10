"""
Production Django settings.

Security-hardened configuration for production deployment.
"""
import os
from .base import *
from decouple import config
import dj_database_url

# ─── Security Settings ────────────────────────────────────────────────────────
DEBUG = False

# Allowed hosts - configure via environment variable
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="aeiou.ai,www.aeiou.ai",
    cast=lambda v: [s.strip() for s in v.split(",")]
)

# Security middleware and headers
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = config("SESSION_COOKIE_SAMESITE", default="Lax")
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = config("CSRF_COOKIE_SAMESITE", default="Lax")
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://aeiou.ai,https://www.aeiou.ai",
    cast=lambda v: [s.strip() for s in v.split(",")]
)

# ─── Database Configuration ───────────────────────────────────────────────────
DATABASE_URL = config("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            ssl_require=config("DB_SSL", default=False, cast=bool),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432", cast=int),
            "OPTIONS": {
                "sslmode": config("DB_SSLMODE", default="prefer"),
            },
            "CONN_MAX_AGE": 60,
        }
    }

# Database connection pooling
DATABASE_POOL_ARGS = {
    "max_overflow": 10,
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# ─── Cache Configuration ───────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 50,
        },
        "KEY_PREFIX": "aeiou_prod",
        "TIMEOUT": 300,
    }
}

# ─── Email Configuration ───────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="AEIOU AI <noreply@aeiou.ai>")
EMAIL_SUBJECT_PREFIX = "[AEIOU AI] "

# ─── Logging Configuration ─────────────────────────────────────────────────────
ENABLE_FILE_LOGGING = config("ENABLE_FILE_LOGGING", default=False, cast=bool)
LOG_FILE_PATH = config("LOG_FILE_PATH", default=str(BASE_DIR / "logs" / "django.log"))
SECURITY_LOG_FILE_PATH = config("SECURITY_LOG_FILE_PATH", default=str(BASE_DIR / "logs" / "security.log"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE_PATH,
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 5,
            "formatter": "json",
        },
        "security": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": SECURITY_LOG_FILE_PATH,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "formatter": "json",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", *(["file"] if ENABLE_FILE_LOGGING else [])],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "core": {
            "handlers": ["console", *(["file"] if ENABLE_FILE_LOGGING else [])],
            "level": "INFO",
            "propagate": False,
        },
        "api": {
            "handlers": ["console", *(["file"] if ENABLE_FILE_LOGGING else [])],
            "level": "INFO",
            "propagate": False,
        },
        "utils.security": {
            "handlers": ["console", *(["security"] if ENABLE_FILE_LOGGING else [])],
            "level": "WARNING",
            "propagate": False,
        },
        "utils.security_middleware": {
            "handlers": ["console", *(["security"] if ENABLE_FILE_LOGGING else [])],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", *(["file"] if ENABLE_FILE_LOGGING else [])],
        "level": "INFO",
    },
}

# ─── Media and Static Files ───────────────────────────────────────────────────
# Use S3 for media files in production
if config("USE_S3", default=False, cast=bool):
    # AWS S3 configuration
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = "private"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    
    # Static files
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    
    # Media files
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
else:
    # Local storage fallback
    MEDIA_ROOT = "/var/www/aeiou/media"
    STATIC_ROOT = "/var/www/aeiou/static"

# ─── CORS Configuration ───────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="https://aeiou.ai,https://www.aeiou.ai",
    cast=lambda v: [s.strip() for s in v.split(",")]
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# ─── Performance Settings ─────────────────────────────────────────────────────
# Enable connection pooling
CONN_MAX_AGE = 60

# Optimize database queries
DATABASES["default"].setdefault("OPTIONS", {}).update({
    "connect_timeout": 10,
    "application_name": "aeiou_production",
})

# Cache optimization
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = "aeiou_prod"
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

# ─── API Settings ───────────────────────────────────────────────────────────────
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "100/hour",
    "user": "1000/hour",
    "burst": "100/minute",
    "standard": "60/minute",
    "strict": "10/minute",
    "upload": "10/hour",
    "auth": "20/hour",
    "chat": "100/hour",
    "task": "200/hour",
    "task_write": "100/hour",
    "conversation": "200/hour",
}

# ─── Celery Configuration ─────────────────────────────────────────────────────
CELERY_BROKER_URL = config("REDIS_URL")
CELERY_RESULT_BACKEND = config("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Production worker settings
CELERY_WORKER_CONCURRENCY = config("CELERY_WORKER_CONCURRENCY", default=4, cast=int)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task routing
CELERY_ROUTES = {
    "core.tasks.send_email": {"queue": "email"},
    "core.tasks.process_document": {"queue": "documents"},
    "core.tasks.generate_ai_response": {"queue": "ai"},
}

# ─── Security Monitoring ─────────────────────────────────────────────────────
# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), vr=(), magnetometer=(), gyroscope=()"
    )
}

# ─── File Upload Settings ───────────────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50MB
FILE_UPLOAD_TEMP_DIR = config("FILE_UPLOAD_TEMP_DIR", default="/tmp")

# ─── AI Service Configuration ───────────────────────────────────────────────────
GOOGLE_AI_API_KEY = config("GOOGLE_AI_API_KEY", default=config("GEMINI_API_KEY", default=""))
GROQ_API_KEY = config("GROQ_API_KEY", default="")
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")

# AI service timeouts
AI_SERVICE_TIMEOUT = config("AI_SERVICE_TIMEOUT", default=30, cast=int)
AI_MAX_RETRIES = config("AI_MAX_RETRIES", default=3, cast=int)

# ─── Monitoring and Analytics ───────────────────────────────────────────────────
# Sentry error tracking
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
                signals_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
        ],
        environment="production",
        traces_sample_rate=0.1,
        send_default_pii=False,
        before_send=lambda event, hint: event,
    )

# Prometheus metrics
PROMETHEUS_ENABLED = True
PROMETHEUS_MULTIPROC_DIR = "/tmp/prometheus_multiproc_dir"

# ─── Feature Flags ─────────────────────────────────────────────────────────────
FEATURE_FLAGS = {
    "ADVANCED_AI_FEATURES": config("FEATURE_ADVANCED_AI", default=True, cast=bool),
    "REAL_TIME_COLLABORATION": config("FEATURE_REAL_TIME", default=False, cast=bool),
    "ADVANCED_ANALYTICS": config("FEATURE_ANALYTICS", default=False, cast=bool),
    "BULK_OPERATIONS": config("FEATURE_BULK", default=True, cast=bool),
}

# ─── Third-party Services ───────────────────────────────────────────────────────
# Analytics service
ANALYTICS_ENABLED = config("ANALYTICS_ENABLED", default=False, cast=bool)
ANALYTICS_API_KEY = config("ANALYTICS_API_KEY", default="")

# Notification service
NOTIFICATION_SERVICE_URL = config("NOTIFICATION_SERVICE_URL", default="")
NOTIFICATION_SERVICE_KEY = config("NOTIFICATION_SERVICE_KEY", default="")

# ─── Backup Settings ───────────────────────────────────────────────────────────
BACKUP_ENABLED = config("BACKUP_ENABLED", default=True, cast=bool)
BACKUP_SCHEDULE = config("BACKUP_SCHEDULE", default="0 2 * * *")  # 2 AM daily
BACKUP_RETENTION_DAYS = config("BACKUP_RETENTION_DAYS", default=30, cast=int)

# S3 backup settings
BACKUP_S3_BUCKET = config("BACKUP_S3_BUCKET", default="")
BACKUP_S3_REGION = config("BACKUP_S3_REGION", default="us-east-1")

# ─── Maintenance Mode ───────────────────────────────────────────────────────────
MAINTENANCE_MODE = config("MAINTENANCE_MODE", default=False, cast=bool)
MAINTENANCE_MESSAGE = config(
    "MAINTENANCE_MESSAGE",
    default="AEIOU AI is currently under maintenance. Please check back soon."
)

# ─── Custom Settings ───────────────────────────────────────────────────────────
# Application version
APP_VERSION = config("APP_VERSION", default="1.0.0")
APP_BUILD_NUMBER = config("APP_BUILD_NUMBER", default="")

# Support contact
SUPPORT_EMAIL = config("SUPPORT_EMAIL", default="support@aeiou.ai")
SUPPORT_PHONE = config("SUPPORT_PHONE", default="")

# Legal notices
PRIVACY_POLICY_URL = config("PRIVACY_POLICY_URL", default="https://aeiou.ai/privacy")
TERMS_OF_SERVICE_URL = config("TERMS_OF_SERVICE_URL", default="https://aeiou.ai/terms")

# ─── Development Overrides (should be empty in production) ─────────────────────
# Ensure no development settings leak into production
if DEBUG:
    raise ImproperlyConfigured("DEBUG mode is not allowed in production!")
