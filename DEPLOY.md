# AEIOU AI — Production Deployment Guide

## 🚀 Quick Deploy to Render (Recommended)

### Step 1: Prepare Your Repository

```bash
# Ensure .venv is removed from git (CRITICAL)
git rm -rf --cached .venv
git add .gitignore
git commit -m "Remove .venv from tracking and update gitignore"

# Verify no sensitive files
git status
# Should NOT show: .env, .venv, db.sqlite3, *.log, media/
```

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Production-ready: clean code, updated docs"
git push origin main
```

### Step 3: Deploy on Render

1. **Create Web Service**:
   - Connect your GitHub repo
   - Name: `aeiou-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

2. **Set Environment Variables** in Render Dashboard:
   ```
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(50))">
   DEBUG=False
   ALLOWED_HOSTS=<your-render-domain>.onrender.com,localhost
   DATABASE_URL=<from Render PostgreSQL>
   GEMINI_API_KEY=<your-key>
   GROQ_API_KEY=<your-key>
   OPENROUTER_API_KEY=<your-key>
   REDIS_URL=<from Render Redis>
   DJANGO_SETTINGS_MODULE=config.settings.prod
   ```

3. **Create PostgreSQL Database** on Render

4. **Create Redis Instance** (optional, for Celery)

### Step 4: Deploy Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

Or connect GitHub repo to Vercel dashboard.

Set environment variable in Vercel:
```
NEXT_PUBLIC_API_BASE_URL=https://<your-render-api>.onrender.com/api/v1
```

---

## 📋 Pre-Deployment Checklist

### Security
- [ ] `.env` file is NOT in git (check: `git ls-files | grep .env`)
- [ ] `.venv/` is NOT in git (check: `git ls-files | grep .venv`)
- [ ] `SECRET_KEY` is generated and unique
- [ ] All API keys are rotated (new keys, not used in dev)
- [ ] `DEBUG=False` for production
- [ ] `ALLOWED_HOSTS` includes production domain

### Database
- [ ] PostgreSQL configured (not SQLite)
- [ ] Database migrations ready: `python manage.py makemigrations`
- [ ] Test migrations: `python manage.py migrate`

### Static/Media Files
- [ ] `python manage.py collectstatic --noinput` works
- [ ] R2/S3 configured OR local storage acceptable

### Frontend
- [ ] `npm run build` succeeds without errors
- [ ] Environment variables set in Vercel/Render
- [ ] API_BASE_URL points to production backend

### Email
- [ ] SMTP credentials configured (not console backend)
- [ ] `DEFAULT_FROM_EMAIL` set to proper domain

---

## 🔒 Environment Variables Reference

### Required (All Deployments)
```bash
SECRET_KEY=<50-char hex string>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
DJANGO_SETTINGS_MODULE=config.settings.prod
```

### Database (PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### AI Providers (at least one)
```bash
GEMINI_API_KEY=<key>
GROQ_API_KEY=<key>
OPENROUTER_API_KEY=<key>
```

### Email (SMTP)
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=AEIOU AI <noreply@yourdomain.com>
```

### File Storage (Cloudflare R2 - Optional)
```bash
R2_ACCESS_KEY=<key>
R2_SECRET_KEY=<secret>
R2_BUCKET_NAME=<bucket>
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
```

---

## 🐛 Troubleshooting

### Build Fails on Render
```
Error: Cannot find module
```
**Fix**: Ensure `requirements.txt` includes all dependencies. Check with:
```bash
pip freeze > requirements.txt
```

### Database Connection Error
```
django.db.utils.OperationalError: could not connect to server
```
**Fix**: Verify `DATABASE_URL` format. Should be:
```
postgresql://user:password@hostname:5432/dbname
```

### Static Files 404
**Fix**: Run collectstatic locally first:
```bash
python manage.py collectstatic --noinput
```

### CORS Errors
**Fix**: Add frontend URL to CORS in prod settings:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
]
```

---

## 📁 Files That Should NOT Be in Git

Verify these are NOT tracked:
```bash
git ls-files | grep -E "(\.env|\.venv|db\.sqlite3|\.log|media/|__pycache__)"
# Should return EMPTY
```

If any found, remove them:
```bash
git rm --cached <file>
git commit -m "Remove sensitive files"
```

---

## ✅ Post-Deployment Verification

1. **Health Check**:
   ```bash
   curl https://your-api.onrender.com/api/v1/health/
   # Should return: {"status": "ok"}
   ```

2. **Frontend Loads**: Visit your Vercel URL, should see login page

3. **Registration Works**: Create test account, receive email

4. **Chat Works**: Send message, get AI response

5. **File Upload**: Upload PDF, verify processing

---

## 🆘 Emergency Rollback

If deployment breaks:

1. **Revert in Render**: Dashboard → Manual Deploy → Deploy Previous Version

2. **Database Rollback**: Render PostgreSQL has automatic backups

3. **Frontend Rollback**: Vercel → Deployments → Rollback

---

**You're ready to deploy! 🚀**
