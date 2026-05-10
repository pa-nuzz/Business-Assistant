import os
from .base import *
from decouple import config

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# Disable HTTPS redirects for local development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Add CORS middleware for development (must be early in middleware stack)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "utils.middleware.IPRateLimitMiddleware",
    "utils.middleware.RequestIDMiddleware",
    "utils.middleware.DeviceFingerprintMiddleware",
    "utils.middleware.SlowQueryLoggingMiddleware",
    "utils.middleware.SecurityHeadersMiddleware",
    "utils.middleware_compression.CompressionMiddleware",
    "utils.middleware_cache.CacheHeadersMiddleware",
]

# Frontend URL
FRONTEND_URL = "http://localhost:3000"

# Email Configuration - Load from environment variables
# When EMAIL_BACKEND is set in .env to smtp backend, SMTP is used directly.
# Falls back to console backend only when not configured.
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="AEIOU AI <noreply@aeiou.ai>")
EMAIL_TIMEOUT = 10  # seconds

# Local development settings - PostgreSQL required even in dev
# Set DATABASE_URL in .env for local dev: postgres://user:pass@localhost:5432/aeiou_dev
_db_url = config("DATABASE_URL", default="")
if not _db_url:
    raise ImproperlyConfigured(
        "DATABASE_URL is required. Set it in your .env file.\n"
        "Example: DATABASE_URL=postgres://user:password@localhost:5432/aeiou_dev"
    )

DATABASES = {
    "default": dj_database_url.parse(_db_url, conn_max_age=600)
}

# Use Redis if available, fallback to eager execution for dev
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "memory://")
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Verbose logging in dev
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
    "loggers": {
        "agents": {"level": "DEBUG"},
        "mcp": {"level": "DEBUG"},
        "services": {"level": "DEBUG"},
    },
}
