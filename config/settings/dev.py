from .base import *

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

# Frontend URL
FRONTEND_URL = "http://localhost:3000"

# Email Configuration - Gmail SMTP
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "anuj.paudel061@gmail.com"
# NOTE: Remove space from app password - should be 16 chars like "hxtozcsjvvghvgvq"
EMAIL_HOST_PASSWORD = "hxtozcsjvvghvgvq"  # Replace with your actual 16-char app password
DEFAULT_FROM_EMAIL = "AEIOU AI <anuj.paudel061@gmail.com>"

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
