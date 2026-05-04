# Deployment

How to get this running in production.

## Docker (Easiest)

```bash
git clone https://github.com/pa-nuzz/aeiou-ai.git
cd aeiou-ai
cp .env.example .env
# Edit .env with your production settings
docker-compose up -d
```

## Manual Deployment

You'll need:
- PostgreSQL 14+
- Redis 7+
- Node.js 20+
- Python 3.12+
- SSL certificate

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb aeiou_production

# Create user
psql -c "CREATE USER aeiou WITH PASSWORD 'secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE aeiou_production TO aeiou;"
```

### 2. Environment Variables

```bash
# Core
SECRET_KEY=<generate-with-django-secret-key-command>
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://aeiou:secure_password@localhost:5432/aeiou_production

# Redis
REDIS_URL=redis://localhost:6379/0

# AI APIs (get from providers)
GEMINI_API_KEY=your-key
GROQ_API_KEY=your-key
OPENROUTER_API_KEY=your-key

# Email (Postmark/SES/SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.postmarkapp.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-server-token
EMAIL_HOST_PASSWORD=your-server-token
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=hello@yourdomain.com

# Storage (AWS S3 or compatible)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=aeiou-uploads
AWS_S3_REGION_NAME=us-east-1
```

### 3. Backend Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start with Gunicorn
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### 4. Frontend Build

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Or with env vars
NEXT_PUBLIC_API_URL=https://api.yourdomain.com npm run build
```

### 5. Celery Workers

```bash
# Worker
 celery -A config worker -l info -c 4

# Beat (for scheduled tasks)
celery -A config beat -l info

# Flower (monitoring)
celery -A config flower --port=5555
```

### 6. Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    # Static files
    location /static/ {
        alias /var/www/aeiou/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/aeiou/media/;
        expires 1d;
    }

    # WebSocket (if using Channels)
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7. Systemd Services

**Backend (`/etc/systemd/system/aeiou-api.service`):**
```ini
[Unit]
Description=AEIOU AI API
After=network.target

[Service]
User=aeiou
Group=aeiou
WorkingDirectory=/opt/aeiou
EnvironmentFile=/opt/aeiou/.env
ExecStart=/opt/aeiou/.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Worker (`/etc/systemd/system/aeiou-worker.service`):**
```ini
[Unit]
Description=AEIOU AI Celery Worker
After=network.target

[Service]
User=aeiou
Group=aeiou
WorkingDirectory=/opt/aeiou
EnvironmentFile=/opt/aeiou/.env
ExecStart=/opt/aeiou/.venv/bin/celery -A config worker -l info -c 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8. Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aeiou-api aeiou-worker
sudo systemctl start aeiou-api aeiou-worker
```

## Health Checks

```bash
# Check API
curl https://yourdomain.com/api/v1/health/

# Check Celery
celery -A config inspect active
```

## When Things Break

| Problem | Fix |
|---------|-----|
| 502 Bad Gateway | Gunicorn not running on port 8000 |
| Static files 404 | Run `collectstatic`, check nginx paths |
| Database errors | Check `DATABASE_URL` format |
| Celery not working | Check Redis connection and worker logs |
| AI errors | Verify API keys in `.env` |
