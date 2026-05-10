#!/bin/bash
set -e

# Oracle Cloud Infrastructure Deployment Script for AEIOU AI
# Usage: ./scripts/deploy-oracle-cloud.sh [staging|production]

ENVIRONMENT=${1:-production}
APP_DIR="/opt/aeiou-ai"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPOSE="docker compose"

if ! docker compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
fi

echo "========================================"
echo "AEIOU AI - Oracle Cloud Deployment"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: ${TIMESTAMP}"
echo "========================================"

# Pre-deployment checks
echo "[1/7] Running pre-deployment checks..."
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found. Run from project root."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "Error: .env not found. Copy .env.example to .env and fill production values."
    exit 1
fi

if grep -q "REPLACE_WITH_GENERATED_SECRET_KEY\\|your_.*_key_here\\|your-domain.com" .env; then
    echo "Error: .env still contains placeholder production values."
    exit 1
fi

# Create backup
echo "[2/7] Creating database backup..."
mkdir -p ${BACKUP_DIR}
${COMPOSE} exec -T db pg_dump -U aeiou_user aeiou > ${BACKUP_DIR}/aeiou_backup_${TIMESTAMP}.sql || true

# Pull latest images
echo "[3/7] Pulling latest Docker images..."
${COMPOSE} pull || true

# Deploy with zero-downtime
echo "[4/7] Deploying services..."
${COMPOSE} up -d --build db redis
${COMPOSE} up -d --no-deps --build backend
${COMPOSE} up -d --no-deps --build celery_worker
${COMPOSE} up -d --no-deps --build frontend
${COMPOSE} up -d nginx

# Run migrations
echo "[5/7] Running database migrations..."
${COMPOSE} exec -T backend python manage.py migrate --noinput

# Collect static files
echo "[6/7] Collecting static files..."
${COMPOSE} exec -T backend python manage.py collectstatic --noinput
${COMPOSE} exec -T backend python manage.py deploy_preflight --json
${COMPOSE} exec -T backend python manage.py ai_preflight --json

# Health checks
echo "[7/7] Running health checks..."
sleep 10
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health/ || echo "000")

if [ "${HEALTH_STATUS}" = "200" ]; then
    echo "========================================"
    echo "Deployment successful!"
    echo "Health check: ${HEALTH_STATUS}"
    echo "========================================"
else
    echo "Warning: Health check returned ${HEALTH_STATUS}"
    echo "Deployment completed but verify services manually."
fi

# Cleanup old backups (keep last 7)
ls -t ${BACKUP_DIR}/aeiou_backup_*.sql 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true

echo "Deployment complete at ${TIMESTAMP}"
