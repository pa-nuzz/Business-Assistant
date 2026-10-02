"""
Celery configuration for the business assistant.
"""
import logging
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.dev"))

app = Celery("business_assistant")
logger = logging.getLogger(__name__)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    "summarize-conversations-daily": {
        "task": "services.tasks.summarize_conversations_task",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
    "cleanup-expired-sessions-daily": {
        "task": "services.tasks.cleanup_expired_sessions_task",
        "schedule": crontab(hour=4, minute=0),  # Run daily at 4 AM
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.debug("Celery debug task request: %r", self.request)
