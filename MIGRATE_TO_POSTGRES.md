# PostgreSQL Migration Guide

## Why You NEED This

SQLite is causing your data loss:
- File locks prevent concurrent writes
- No transaction safety
- Data corruption on crashes
- Cannot scale beyond 1 user

## Migration Steps

### 1. Install PostgreSQL (Mac)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb aeiou_ai

# Create user
psql postgres -c "CREATE USER aeiou_user WITH PASSWORD 'your_secure_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE aeiou_ai TO aeiou_user;"
```

### 2. Update .env

```bash
# Delete SQLite settings
# DATABASE_URL=db.sqlite3  ← DELETE THIS

# Add PostgreSQL
DATABASE_URL=postgres://aeiou_user:your_secure_password@localhost:5432/aeiou_ai
DB_NAME=aeiou_ai
DB_USER=aeiou_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Install psycopg2

```bash
pip install psycopg2-binary
```

### 4. Update config/settings/dev.py

Already done — `DATABASE_URL` now uses PostgreSQL.

### 5. Delete SQLite Database

```bash
# Delete the problematic SQLite file
rm db.sqlite3
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Test

```bash
python manage.py runserver
```

## Verify Data Persistence

1. Update profile → Check it saves
2. Log out → Log in → Profile should persist
3. Change password → Should work
4. Upload document → Should process

## Production (Render)

For Render.com deployment, the `render.yaml` already includes PostgreSQL:

```yaml
databases:
  - name: aeiou-db
    databaseName: aeiou_ai
    user: aeiou
```

The `DATABASE_URL` is automatically set.
