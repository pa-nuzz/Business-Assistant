# AEIOU AI - Operations Runbooks

## Table of Contents
1. [Service Health Checks](#service-health-checks)
2. [Deployment Procedures](#deployment-procedures)
3. [Incident Response](#incident-response)
4. [Database Operations](#database-operations)
5. [Cache Operations](#cache-operations)
6. [Vector Search Operations](#vector-search-operations)
7. [Authentication & Sessions](#authentication--sessions)
8. [Async Task Queue](#async-task-queue)
9. [Monitoring & Alerting](#monitoring--alerting)
10. [Backup & Recovery](#backup--recovery)
11. [Security Incidents](#security-incidents)
12. [Performance Tuning](#performance-tuning)

---

## Service Health Checks

### Liveness Probe
```bash
curl -f http://localhost:8000/health/
# Expected: 200 OK with {"status": "healthy"}
```

### Readiness Probe
```bash
curl -f http://localhost:8000/health/ready/
# Checks: Database, Redis, pgvector
# Expected: 200 OK with {"status": "ready", "checks": {...}}
```

### Startup Probe
```bash
curl -f http://localhost:8000/health/startup/
# Expected: 200 OK after migrations complete
```

### Manual Health Verification
```bash
# Check Django is responding
python manage.py check --deploy

# Check database connectivity
python manage.py dbshell -c "SELECT 1;"

# Check Redis
redis-cli ping

# Check pgvector
python -c "from pgvector.django import VectorField; print('pgvector OK')"

# Check Celery workers
celery -A config inspect ping
```

---

## Deployment Procedures

### Staging (Railway) - Automatic
```bash
# Triggered on push to develop branch
# 1. Railway detects push
# 2. Builds Docker image
# 3. Runs migrations
# 4. Deploys to staging environment
# 5. Runs smoke tests

# Manual trigger:
railway up --environment staging
```

### Production (AWS ECS) - Manual Approval Required
```bash
# 1. Create release tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# 2. GitHub Actions workflow triggers
# 3. Build and push Docker image to ECR
# 4. Run database migrations (separate task)
# 5. Deploy to ECS with blue/green
# 6. Run post-deployment smoke tests
# 7. Manual approval for traffic switch

# Rollback:
aws ecs update-service --cluster production --service django --task-definition <previous-task-def>
```

### Database Migrations
```bash
# Always run migrations BEFORE deploying new code
# Staging:
railway run python manage.py migrate

# Production:
aws ecs run-task --cluster production --task-definition migrate --overrides '{"containerOverrides": [{"name": "migrate", "command": ["python", "manage.py", "migrate"]}]}'

# Verify migration state:
python manage.py showmigrations --plan
```

### Pre-deployment Checklist
- [ ] All tests pass (88 tests)
- [ ] Lint passes (ruff, mypy, black)
- [ ] Frontend builds successfully
- [ ] OpenAPI schema generated
- [ ] Database migration reviewed
- [ ] Changelog updated
- [ ] Security scan passed

---

## Incident Response

### Severity Levels
| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| SEV-1 | Complete outage, data loss | 15 min | DB down, API 5xx > 50% |
| SEV-2 | Major functionality broken | 1 hour | Chat broken, auth failing |
| SEV-3 | Minor issue, workaround exists | 4 hours | Slow search, UI bug |
| SEV-4 | Low impact, cosmetic | Next sprint | Typo, minor styling |

### Incident Response Flow
```
1. DETECT → Alert fires (Datadog/PagerDuty)
2. ACKNOWLEDGE → On-call acknowledges (5 min)
3. TRIAGE → Check dashboards, logs, runbooks
4. MITIGATE → Apply workaround/fix
5. RESOLVE → Root cause fixed, verified
6. POSTMORTEM → Write incident report (within 48h)
```

### Common Incidents & Solutions

#### API Returns 500 Errors
```bash
# 1. Check recent deployments
git log --oneline -10

# 2. Check error logs
# Railway: railway logs
# AWS: CloudWatch Logs / Datadog

# 3. Common causes:
# - Database migration not run
# - Redis connection failed
# - pgvector extension missing
# - Environment variable missing

# 4. Quick mitigation:
# - Rollback to previous version
# - Restart service: railway restart / aws ecs update-service --force-new-deployment
```

#### Database Connection Pool Exhausted
```bash
# Symptoms: "connection pool exhausted", slow queries
# 1. Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

# 2. Check for long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '30 seconds';

# 3. Kill stuck queries
SELECT pg_terminate_backend(pid);

# 4. Increase pool size (temporary)
# Edit config/settings/production.py: CONN_MAX_AGE, POOL_SIZE
```

#### Redis Memory High
```bash
# 1. Check memory usage
redis-cli INFO memory

# 2. Check key distribution
redis-cli --bigkeys

# 3. Clear expired keys
redis-cli FLUSHALL ASYNC  # CAUTION: clears all cache

# 4. Better: selective cleanup
redis-cli SCAN 0 MATCH "session:*" COUNT 1000 | xargs redis-cli DEL
```

#### pgvector Search Slow
```bash
# 1. Check index status
SELECT * FROM pg_indexes WHERE tablename = 'core_documentchunk';

# 2. Rebuild HNSW index if needed
DROP INDEX IF EXISTS core_documentchunk_embedding_idx;
CREATE INDEX core_documentchunk_embedding_idx ON core_documentchunk USING hnsw (embedding vector_cosine_ops);

# 3. Analyze table
ANALYZE core_documentchunk;
```

---

## Database Operations

### Connect to Production Database
```bash
# Via AWS Session Manager (bastion)
aws ssm start-session --target <bastion-instance-id>

# Or use Railway CLI for staging
railway connect postgresql
```

### Common Queries

#### Check Table Sizes
```sql
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Find Slow Queries
```sql
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

#### Check Index Usage
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
```

#### Vacuum/Analyze
```bash
# Manual vacuum (run during low traffic)
python manage.py dbshell -c "VACUUM ANALYZE;"

# Or specific table
python manage.py dbshell -c "VACUUM ANALYZE core_task;"
```

### Schema Changes
```bash
# 1. Create migration locally
python manage.py makemigrations --name descriptive_name

# 2. Review migration file
cat core/migrations/00XX_descriptive_name.py

# 3. Test on staging
railway run python manage.py migrate

# 4. Deploy with migration
# Migration runs automatically in CI/CD before deploy
```

### Data Fixes (Use with Caution)
```bash
# Always test on staging first!
# 1. Backup table
pg_dump -t core_task -d aeoiu_staging > task_backup.sql

# 2. Run fix in transaction
python manage.py shell -c "
from django.db import transaction
from core.models import Task
with transaction.atomic():
    Task.objects.filter(status='invalid').update(status='todo')
"

# 3. Verify
python manage.py shell -c "from core.models import Task; print(Task.objects.filter(status='invalid').count())"
```

---

## Cache Operations

### Redis Commands
```bash
# Connect
redis-cli -h <redis-host> -p 6379 -a <password>

# Check memory
INFO memory

# Check connected clients
CLIENT LIST

# Clear specific pattern
# CAUTION: Use SCAN not KEYS in production
redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL

# Monitor commands (debugging)
MONITOR

# Slow log
SLOWLOG GET 10
```

### Cache Invalidation
```bash
# Invalidate workspace context
redis-cli DEL "workspace_context:<workspace_id>"

# Invalidate user sessions
redis-cli DEL "session:<session_key>"

# Invalidate document search cache
redis-cli --scan --pattern "search:*<document_id>*" | xargs redis-cli DEL

# Full cache clear (emergency only)
redis-cli FLUSHALL ASYNC
```

### Redis Configuration Tuning
```bash
# Check current config
CONFIG GET maxmemory
CONFIG GET maxmemory-policy

# Set memory policy (requires restart)
CONFIG SET maxmemory-policy allkeys-lru
CONFIG REWRITE
```

---

## Vector Search Operations

### pgvector Index Management
```bash
# Check index status
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute(\"SELECT * FROM pg_indexes WHERE tablename = 'core_documentchunk'\")
    for row in c.fetchall():
        print(row)
"

# Rebuild HNSW index (run during low traffic)
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('DROP INDEX IF EXISTS core_documentchunk_embedding_idx')
    c.execute('''
        CREATE INDEX core_documentchunk_embedding_idx
        ON core_documentchunk USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ')
    print('Index rebuilt')
"

# Check index size
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute(\"SELECT pg_size_pretty(pg_relation_size('core_documentchunk_embedding_idx'))\")
    print(c.fetchone())
"
```

### Embedding Regeneration
```bash
# Regenerate all embeddings (background task)
python manage.py shell -c "
from core.tasks import regenerate_all_embeddings
regenerate_all_embeddings.delay()
"

# Regenerate for specific workspace
python manage.py shell -c "
from core.tasks import regenerate_workspace_embeddings
regenerate_workspace_embeddings.delay(workspace_id='<uuid>')
"

# Check embedding coverage
python manage.py shell -c "
from core.models import DocumentChunk
total = DocumentChunk.objects.count()
with_embedding = DocumentChunk.objects.exclude(embedding=None).count()
print(f'Coverage: {with_embedding}/{total} ({with_embedding/total*100:.1f}%)')
"
```

---

## Authentication & Sessions

### Token Management
```bash
# List active sessions for user
python manage.py shell -c "
from core.models import Session
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='user@example.com')
sessions = Session.objects.filter(user=user, revoked_at__isnull=True)
for s in sessions:
    print(f'{s.id} - {s.user_agent} - {s.ip_address} - {s.created_at}')
"

# Revoke all sessions for user (force logout)
python manage.py shell -c "
from core.models import Session
from django.utils import timezone
Session.objects.filter(user_id='<user_id>', revoked_at__isnull=True).update(revoked_at=timezone.now())
"

# Cleanup expired sessions (run via cron)
python manage.py shell -c "
from core.models import Session
from django.utils import timezone
Session.objects.filter(expires_at__lt=timezone.now()).delete()
"
```

### API Token Management
```bash
# List tokens for workspace
python manage.py shell -c "
from core.models import APIToken
tokens = APIToken.objects.filter(workspace_id='<workspace_id>')
for t in tokens:
    print(f'{t.name} - {t.created_by} - {t.last_used_at} - {t.revoked_at}')
"

# Revoke compromised token
python manage.py shell -c "
from core.models import APIToken
APIToken.objects.filter(id='<token_id>').update(revoked_at=timezone.now())
"
```

---

## Async Task Queue

### Celery Management
```bash
# Check worker status
celery -A config inspect ping

# Check active tasks
celery -A config inspect active

# Check scheduled tasks
celery -A config inspect scheduled

# Check registered tasks
celery -A config inspect registered

# Purge queue (emergency)
celery -A config purge

# Restart workers
# Railway: railway restart worker
# AWS: aws ecs update-service --cluster production --service celery-worker --force-new-deployment
```

### Queue Monitoring
```bash
# Check queue lengths
redis-cli LLEN celery:default
redis-cli LLEN celery:documents
redis-cli LLEN celery:embeddings
redis-cli LLEN celery:notifications

# Monitor queue in real-time
watch -n 1 'redis-cli LLEN celery:default'
```

### Stuck Task Recovery
```bash
# Find stuck tasks
celery -A config inspect active | jq '.[] | .[] | select(.time_start < (now - 300))'

# Revoke stuck task
celery -A config control revoke <task_id> --terminate

# Re-queue failed task
python manage.py shell -c "
from core.tasks import process_document
process_document.delay(document_id='<uuid>')
"
```

---

## Monitoring & Alerting

### Key Dashboards
- **API Health**: Request rate, latency, error rate
- **Database**: Connections, query latency, replication lag
- **Cache**: Hit rate, memory, evictions
- **Queue**: Depth, processing rate, failures
- **Vector Search**: Query latency, index size
- **Business**: Active users, tasks created, documents processed

### Critical Alerts
| Alert | Condition | Severity | Runbook |
|-------|-----------|----------|---------|
| APIErrorRateHigh | 5xx > 5% for 5min | SEV-1 | Check logs, rollback |
| DatabaseConnectionsHigh | > 80% pool used | SEV-2 | Check for leaks, scale |
| RedisMemoryHigh | > 85% memory used | SEV-2 | Clear cache, scale |
| CeleryQueueBacklog | > 1000 tasks for 10min | SEV-2 | Scale workers |
| VectorSearchSlow | p95 > 2s | SEV-3 | Rebuild index |
| DiskSpaceLow | > 85% used | SEV-1 | Cleanup, expand |

### Log Analysis
```bash
# Search errors in last hour
# Railway:
railway logs --tail 1000 | grep -i error

# AWS CloudWatch:
aws logs filter-log-events --log-group-name /ecs/django --start-time $(date -d '1 hour ago' +%s)000 --filter-pattern ERROR

# Structured log query (Datadog)
@service:django @status:error | tail 100
```

---

## Backup & Recovery

### Automated Backups
- **PostgreSQL**: Daily snapshots (AWS RDS) / Continuous (Railway)
- **Redis**: AOF persistence (every 1 sec)
- **Media files**: S3 versioning enabled

### Manual Backup
```bash
# Database dump
pg_dump -h <host> -U <user> -d aeoiu_prod \
  --no-owner --no-privileges --clean --if-exists \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip backup_*.sql

# Upload to S3
aws s3 cp backup_*.sql.gz s3://aeoiu-backups/database/
```

### Recovery Procedures

#### Point-in-Time Recovery (RDS)
```bash
# AWS Console → RDS → Restore to point in time
# Or CLI:
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier aeoiu-prod \
  --target-db-instance-identifier aeoiu-prod-restored \
  --restore-time 2024-01-15T10:30:00.000Z
```

#### Full Database Restore
```bash
# 1. Create new DB
createdb aeoiu_restore

# 2. Restore dump
gunzip -c backup_20240115_103000.sql.gz | psql -d aeoiu_restore

# 3. Run migrations (if schema differs)
python manage.py migrate --database=restore

# 4. Swap DNS / update config
```

#### Media Files Restore
```bash
# Sync from S3
aws s3 sync s3://aeoiu-media/ media/ --delete
```

---

## Security Incidents

### Compromised API Token
```bash
# 1. Immediately revoke token
python manage.py shell -c "
from core.models import APIToken
from django.utils import timezone
APIToken.objects.filter(key_hash='<compromised_hash>').update(revoked_at=timezone.now())
"

# 2. Check token usage (audit log)
# Query webhook deliveries, API access logs

# 3. Rotate any secrets the token had access to
# Generate new webhook secrets, API keys
```

### Suspicious Login Activity
```bash
# Check recent logins
python manage.py shell -c "
from core.models import Session
from django.utils import timezone
from datetime import timedelta
recent = Session.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24))
for s in recent:
    print(f'{s.user.email} - {s.ip_address} - {s.user_agent} - {s.created_at}')
"

# Block IP (at load balancer / WAF)
# AWS WAF: Add IP to block list
```

### Data Breach Response
1. **Contain**: Revoke all sessions, rotate all secrets
2. **Assess**: Determine scope (what data, how many users)
3. **Notify**: Legal, affected users (per GDPR/CCPA)
4. **Remediate**: Fix vulnerability, improve monitoring
5. **Document**: Postmortem, update runbooks

---

## Performance Tuning

### Database Optimization
```bash
# 1. Enable pg_stat_statements (if not already)
# In postgresql.conf: shared_preload_libraries = 'pg_stat_statements'

# 2. Identify slow queries
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('''
        SELECT query, mean_time, calls, total_time
        FROM pg_stat_statements
        WHERE mean_time > 100
        ORDER BY mean_time DESC LIMIT 10
    ''')
    for row in c.fetchall():
        print(f'{row[1]:.2f}ms x{row[2]} = {row[3]:.2f}ms total')
        print(f'  {row[0][:200]}...')
        print()
"

# 3. Add missing indexes
# Example: CREATE INDEX ON core_task (workspace_id, status, assignee_id);

# 4. Partition large tables
# TaskActivity, Message tables by month
```

### API Response Optimization
```bash
# Enable response compression
# settings.py: MIDDLEWARE includes 'django.middleware.gzip.GZipMiddleware'

# Add database indexes for common filters
# Check: EXPLAIN ANALYZE SELECT ... WHERE workspace_id=... AND status=...

# Use select_related/prefetch_related in views
# Check: django-debug-toolbar or silk profiler
```

### Frontend Performance
```bash
# Build analysis
cd frontend && npm run build && npm run analyze

# Check bundle size
# Target: < 200KB gzipped initial JS

# Enable caching headers
# nginx/ALB: Cache-Control: public, max-age=31536000, immutable for static assets
```

---

## Contact Information

### On-Call Rotation
- Primary: [Name] - [Phone] - [Slack]
- Secondary: [Name] - [Phone] - [Slack]

### Escalation Path
1. On-call engineer (15 min)
2. Team lead (30 min)
3. Engineering manager (1 hour)
4. CTO (2 hours)

### External Vendors
- **Railway**: support@railway.app
- **AWS Support**: Business tier - 1-hour response
- **Anthropic**: API issues - support@anthropic.com
- **OpenAI**: API issues - support@openai.com

---

## Runbook Maintenance

- Review quarterly
- Update after each incident
- Test procedures annually
- Version control in `/docs/runbooks/`