# AEIOU AI - Deployment Guide

## Overview

This guide covers deployment of AEIOU AI in various environments, from local development to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Development](#docker-development)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python**: 3.12+
- **Node.js**: 18+
- **Docker**: 20.10+ (for containerized deployment)
- **PostgreSQL**: 13+ (production)
- **Redis**: 6+ (production)

### Required Services
- PostgreSQL database
- Redis cache
- SMTP server (for emails)
- Object storage (S3 or compatible)

## Local Development Setup

### 1. Backend Setup

```bash
# Clone the repository
git clone <repository-url>
cd aeiou-ai

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Configure environment variables
nano .env
```

### 2. Environment Configuration (.env)

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL required)
DATABASE_URL=postgres://user:password@localhost:5432/aeiou_dev

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AI Services
GOOGLE_AI_API_KEY=your-google-ai-key
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend
FRONTEND_URL=http://localhost:3000

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata fixtures/initial_data.json
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Configure frontend environment
nano .env.local
```

### 5. Frontend Environment (.env.local)

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/
NEXT_PUBLIC_APP_NAME=AEIOU AI
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 6. Running the Application

```bash
# Terminal 1: Backend
cd /path/to/aeiou-ai
source .venv/bin/activate
python manage.py runserver

# Terminal 2: Celery Worker
cd /path/to/aeiou-ai
source .venv/bin/activate
celery -A config worker -l info

# Terminal 3: Frontend
cd /path/to/aeiou-ai/frontend
npm run dev
```

### 7. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## Docker Development

### 1. Docker Compose Setup

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aeiou_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - .venv:/app/.venv
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://postgres:postgres@db:5432/aeiou_dev
      - REDIS_URL=redis://redis:6379/0

  celery:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - .venv:/app/.venv
    depends_on:
      - db
      - redis
    command: celery -A config worker -l info
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/aeiou_dev
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

volumes:
  postgres_data:
```

### 2. Docker Development Files

**Dockerfile.dev** (Backend):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create virtual environment
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Dockerfile.dev** (Frontend):
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

### 3. Running Docker Development

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## Staging Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Staging Docker Compose

Create `docker-compose.staging.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aeiou_staging
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  backend:
    image: aeiou-ai/backend:staging
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@db:5432/aeiou_staging
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${DOMAIN}
    restart: unless-stopped

  celery:
    image: aeiou-ai/backend:staging
    depends_on:
      - db
      - redis
    command: celery -A config worker -l info
    environment:
      - DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@db:5432/aeiou_staging
      - REDIS_URL=redis://redis:6379/0
    restart: unless-stopped

  frontend:
    image: aeiou-ai/frontend:staging
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. Nginx Configuration

Create `nginx/staging.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name staging.aeiou.ai;

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

### 4. Deployment Script

Create `deploy-staging.sh`:

```bash
#!/bin/bash

set -e

echo "Deploying to staging..."

# Load environment variables
source .env.staging

# Build and push images
docker build -t aeiou-ai/backend:staging .
docker build -t aeiou-ai/frontend:staging ./frontend

# Deploy to server
scp docker-compose.staging.yml .env.staging user@staging-server:/home/user/
ssh user@staging-server "cd /home/user && docker-compose -f docker-compose.staging.yml down"
ssh user@staging-server "cd /home/user && docker-compose -f docker-compose.staging.yml up -d"

# Run migrations
ssh user@staging-server "docker-compose -f docker-compose.staging.yml exec backend python manage.py migrate"

# Collect static files
ssh user@staging-server "docker-compose -f docker-compose.staging.yml exec backend python manage.py collectstatic --noinput"

echo "Staging deployment complete!"
```

## Production Deployment

### 1. Production Architecture

```
Load Balancer (Nginx/HAProxy)
    ↓
Application Servers (3+ instances)
    ↓
PostgreSQL (Primary + Read Replicas)
    ↓
Redis Cluster
    ↓
Object Storage (S3)
```

### 2. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aeiou_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      replicas: 1

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    deploy:
      replicas: 1

  backend:
    image: aeiou-ai/backend:latest
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@db:5432/aeiou_prod
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${DOMAIN}
      - SENTRY_DSN=${SENTRY_DSN}
    restart: unless-stopped
    deploy:
      replicas: 3

  celery:
    image: aeiou-ai/backend:latest
    depends_on:
      - db
      - redis
    command: celery -A config worker -l info
    environment:
      - DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@db:5432/aeiou_prod
      - REDIS_URL=redis://redis:6379/0
    restart: unless-stopped
    deploy:
      replicas: 2

  frontend:
    image: aeiou-ai/frontend:latest
    restart: unless-stopped
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    deploy:
      replicas: 1

volumes:
  postgres_data:
```

### 3. SSL/TLS Setup

```bash
# Obtain SSL certificate
sudo certbot --nginx -d aeiou.ai -d www.aeiou.ai

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Production Deployment Script

Create `deploy-production.sh`:

```bash
#!/bin/bash

set -e

echo "Deploying to production..."

# Load environment variables
source .env.production

# Build and tag images
docker build -t aeiou-ai/backend:latest .
docker build -t aeiou-ai/frontend:latest ./frontend

# Tag for registry
docker tag aeiou-ai/backend:latest registry.example.com/aeiou-ai/backend:latest
docker tag aeiou-ai/frontend:latest registry.example.com/aeiou-ai/frontend:latest

# Push to registry
docker push registry.example.com/aeiou-ai/backend:latest
docker push registry.example.com/aeiou-ai/frontend:latest

# Deploy to production servers
for server in server1 server2 server3; do
    scp docker-compose.prod.yml .env.production user@$server:/opt/aeiou-ai/
    ssh user@$server "cd /opt/aeiou-ai && docker-compose -f docker-compose.prod.yml pull"
    ssh user@$server "cd /opt/aeiou-ai && docker-compose -f docker-compose.prod.yml up -d"
done

# Run migrations on one server
ssh user@server1 "docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate"

# Collect static files
ssh user@server1 "docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput"

echo "Production deployment complete!"
```

## Oracle Cloud Deployment

### Prerequisites
- Oracle Cloud Infrastructure (OCI) account
- OCI Compute Instance (VM.Standard.E4.Flex recommended)
- OCI Object Storage bucket (optional, for media files)
- Block Volume for PostgreSQL data (recommended)

### 1. Infrastructure Setup

```bash
# Create a compartment
oci iam compartment create --name aeiou-ai --description "AEIOU AI Production"

# Create a VCN and subnet
oci network vcn create --cidr-block 10.0.0.0/16 --display-name aeiou-vcn

# Create a compute instance
oci compute instance launch \
  --availability-domain $(oci iam availability-domain list -c ${COMPARTMENT_ID} --query "data[0].name" --raw-output) \
  --compartment-id ${COMPARTMENT_OCID} \
  --shape VM.Standard.E4.Flex \
  --shape-config '{"ocpus": 2, "memoryInGBs": 16}' \
  --display-name aeiou-app \
  --subnet-id ${SUBNET_OCID} \
  --image-id ${IMAGE_OCID} \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub
```

### 2. Instance Configuration

```bash
# SSH into the instance
ssh -i ~/.ssh/oci_key opc@${INSTANCE_IP}

# Install Docker and Docker Compose
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker opc

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app directory
sudo mkdir -p /opt/aeiou-ai
sudo chown opc:opc /opt/aeiou-ai
```

### 3. Deploy Application

```bash
cd /opt/aeiou-ai

# Clone repository
git clone https://github.com/pa-nuzz/aeiou-ai.git .

# Copy environment file
cp .env.example .env
# Edit .env with production settings

# Run deployment script
bash scripts/deploy-oracle-cloud.sh production
```

### 4. OCI Security Configuration

- **Security Lists**: Allow ports 80, 443, 8000 from your IP only
- **Network Security Groups**: Restrict database access to compute instance
- **IAM Policies**: Create a dedicated deployment user with minimal privileges
- **Secrets**: Use OCI Vault for managing API keys and database passwords

### 5. Monitoring on OCI

- **Logging**: Enable OCI Logging service for container logs
- **Monitoring**: Set up OCI Monitoring alarms for CPU/memory thresholds
- **Notifications**: Configure OCI Notifications for alerts

---

## Environment Configuration

### Development Environment
```bash
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/aeiou_dev
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Staging Environment
```bash
DEBUG=False
DATABASE_URL=postgres://user:pass@staging-db:5432/aeiou_staging
REDIS_URL=redis://staging-redis:6379/0
ALLOWED_HOSTS=staging.aeiou.ai
CORS_ALLOWED_ORIGINS=https://staging.aeiou.ai
```

### Production Environment
```bash
DEBUG=False
DATABASE_URL=postgres://user:pass@prod-db:5432/aeiou_prod
REDIS_URL=redis://prod-redis:6379/0
ALLOWED_HOSTS=aeiou.ai,www.aeiou.ai
CORS_ALLOWED_ORIGINS=https://aeiou.ai,https://www.aeiou.ai
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

## Monitoring & Maintenance

### 1. Health Checks

```bash
# Backend health
curl https://aeiou.ai/api/v1/health/

# Database health
python manage.py db_health_check

# Redis health
redis-cli ping
```

### 2. Log Monitoring

```bash
# Application logs
docker-compose logs -f backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u docker -f
```

### 3. Backup Strategy

```bash
# Database backup
pg_dump aeiou_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup
aws s3 sync s3://aeiou-media/ ./backup/media/

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env* nginx/ docker-compose*.yml
```

### 4. Performance Monitoring

- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Dashboard visualization
- **New Relic**: APM (optional)

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database status
docker-compose exec db pg_isready

# Check connection string
echo $DATABASE_URL

# Test connection
python manage.py dbshell
```

#### 2. Redis Connection Errors
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

#### 3. Application Startup Issues
```bash
# Check application logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep DATABASE_URL

# Run health check
docker-compose exec backend python manage.py check
```

#### 4. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test Nginx configuration
sudo nginx -t
```

### Performance Issues

#### 1. Slow Database Queries
```bash
# Enable query logging
python manage.py shell
>>> from django.db import connection
>>> connection.queries_log_enabled = True

# Analyze slow queries
python manage.py dbshell
> SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

#### 2. High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart backend
```

#### 3. Cache Issues
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Check cache hit rate
docker-compose exec redis redis-cli INFO stats
```

### Emergency Procedures

#### 1. Application Down
```bash
# Restart all services
docker-compose restart

# Check logs
docker-compose logs -f

# Rollback deployment
docker-compose down
docker-compose up -d --force-recreate
```

#### 2. Database Issues
```bash
# Enter maintenance mode
# Update nginx to return 503

# Restore from backup
psql aeiou_prod < backup_latest.sql

# Exit maintenance mode
# Restore nginx configuration
```

#### 3. Security Incident
```bash
# Change all secrets
# Rotate API keys
# Update passwords
# Review access logs
# Enable additional monitoring
```

---

For additional support, refer to the [Architecture Documentation](./ARCHITECTURE.md) or contact the development team.
