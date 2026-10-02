#!/usr/bin/env bash
# Bootstrap the local test database requirements.
#
# Django's test runner creates `test_<dbname>` on the fly (the app role needs
# CREATEDB, see below), but the pgvector migrations run
# `CREATE EXTENSION IF NOT EXISTS vector`, which requires superuser.
#
# We install pgvector on the `template1` database once: every database that is
# later created (including each `test_<dbname>`) inherits the `vector`
# extension, so the migration succeeds without giving the app role superuser.
#
# Requires: local Postgres superuser on the default socket (peer auth).
# Idempotent - safe to re-run.
set -euo pipefail

DB_SUPERUSER="${PGUSER:-$(whoami)}"

echo ">>> Installing pgvector on template1 (superuser: ${DB_SUPERUSER})"
psql -U "${DB_SUPERUSER}" -d template1 -qc "CREATE EXTENSION IF NOT EXISTS vector;"

echo ">>> Ensuring the application DB role can create test databases (CREATEDB)"
# Reads the app role from DATABASE_URL in the repo .env, if present.
DB_URL="${DATABASE_URL:-$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)}"
APP_ROLE="$(python3 - "$DB_URL" <<'PY'
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1] or "")
print(u.username or "")
PY
)"

if [[ -n "${APP_ROLE}" ]]; then
    psql -U "${DB_SUPERUSER}" -d postgres -qc "ALTER ROLE ${APP_ROLE} CREATEDB;"
else
    echo ">>> Warning: DATABASE_URL not found; skipping CREATEDB grant."
fi

echo ">>> Done. Run tests with: python manage.py test  (or pytest)"