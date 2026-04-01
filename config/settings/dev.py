from .base import *

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

# Frontend URL for password reset links
FRONTEND_URL = "http://localhost:3000"

# Email Configuration (console backend for development - prints to terminal)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@aeiou-ai.com"

# For production, use SMTP:
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = "your-email@gmail.com"
# EMAIL_HOST_PASSWORD = "your-app-password"

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
