import os
from .base import *
from decouple import config

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

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
# For development, you can use console backend or configure SMTP via .env
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Business Assistant <noreply@localhost>")

# Local development settings - uses Postgres via DATABASE_URL
# Set DATABASE_URL in .env for local dev: postgres://user:pass@localhost:5432/aeiou_dev
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
    )
}

# Use Redis if available, fallback to memory for dev
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "memory://")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "memory://")

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
