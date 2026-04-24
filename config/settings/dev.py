from .base import *
from decouple import config

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

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

# Disable Redis for local development - use local memory instead
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "memory://"
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

# SQLite for local dev (no Postgres setup needed)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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
