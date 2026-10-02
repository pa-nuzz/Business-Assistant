from .dev import *  # noqa: F401,F403

# Test settings.
# Inherits everything from dev (Postgres via DATABASE_URL in .env), then
# swaps out side-effectful infra so tests are hermetic and fast:
#   - locmem cache instead of Redis (no shared throttle/rate-limit state)
#   - eager Celery (tasks run inline, no broker needed)
#   - locmem email backend (no console spam)
DEBUG = False

DATABASES["default"] = dj_database_url.parse(  # noqa: F405
    config("DATABASE_URL", default=""),  # noqa: F405
    conn_max_age=0,
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Deterministic, fast password hashing for tests.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Allow testserver for Django test client
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]