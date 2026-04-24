# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for AEIOU AI.

## Backup Strategy

### Automated Backups
- **Schedule**: Daily at 3:00 AM UTC
- **Tool**: django-dbbackup with S3 storage
- **Retention**: 7 daily database backups, 3 media backups
- **Storage**: S3 bucket (`BACKUP_BUCKET` env var)

### Manual Backup Commands

```bash
# Create database backup
python manage.py dbbackup

# Create media backup
python manage.py mediabackup

# Backup with compression
python manage.py dbbackup --compress

# Clean old backups
python manage.py dbbackup --clean
```

## Restore Procedures

### Database Restore

1. **List available backups**:
   ```bash
   python manage.py dbbackup --list
   ```

2. **Restore from latest backup**:
   ```bash
   python manage.py dbrestore
   ```

3. **Restore from specific backup**:
   ```bash
   python manage.py dbrestore -f backup-2024-01-15-030000.dump
   ```

4. **Restore without confirmation** (automation):
   ```bash
   python manage.py dbrestore -n
   ```

### Media Files Restore

```bash
# Restore media files
python manage.py mediarestore
```

## Disaster Scenarios

### Scenario 1: Database Corruption

1. Stop the application:
   ```bash
   # On Render/Railway: scale down web service
   # On VPS: stop gunicorn/celery
   ```

2. Restore from last known good backup:
   ```bash
   python manage.py dbrestore
   ```

3. Verify data integrity:
   ```bash
   python manage.py check --deploy
   python manage.py migrate --check
   ```

4. Restart application

### Scenario 2: Accidental Data Deletion

If soft-deleted (within 30 days):
```python
# In Django shell
from core.models import Task, Document, Conversation

# Restore soft-deleted task
Task.all_objects.get(id='task-uuid').restore()

# List all soft-deleted items
Task.all_objects.filter(deleted_at__isnull=False)
```

If hard-deleted, use database restore procedure above.

### Scenario 3: Complete Infrastructure Loss

1. Provision new infrastructure (Render/Railway/VPS)
2. Set environment variables (DATABASE_URL, AWS credentials, etc.)
3. Deploy application code
4. Run database restore:
   ```bash
   python manage.py dbrestore
   ```
5. Run media restore:
   ```bash
   python manage.py mediarestore
   ```
6. Run migrations if needed:
   ```bash
   python manage.py migrate
   ```
7. Verify: `python manage.py check --deploy`

## Environment Variables Required for Restore

```bash
# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname

# S3 Backup Storage
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
BACKUP_BUCKET=aeiou-backups
AWS_REGION=us-east-1

# Application
SECRET_KEY=xxx
DEBUG=False
```

## Monitoring & Alerts

- Backup success/failure logged to application logs
- S3 bucket should have lifecycle policies
- Test restore monthly on staging environment

## Contact & Escalation

- Primary: DevOps team
- Secondary: Platform provider support (Render/Railway/AWS)

---

Last updated: 2024
