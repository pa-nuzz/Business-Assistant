from .base import *

DEBUG = False

# Security headers for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000

# Cloudflare R2 (S3-compatible) file storage
# R2 free tier: 10GB storage, 1M requests/month
if config('R2_ACCESS_KEY', default=None):
    INSTALLED_APPS += ['storages']
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL', default='https://<accountid>.r2.cloudflarestorage.com')
    AWS_ACCESS_KEY_ID = config('R2_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = config('R2_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME')
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_ADDRESSING_STYLE = 'virtual'

# Simple console logging for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "agents": {"level": "INFO"},
        "mcp": {"level": "INFO"},
        "services": {"level": "INFO"},
    },
}
