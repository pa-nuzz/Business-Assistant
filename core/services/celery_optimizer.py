"""Celery Optimizer - Task queue tuning and batch processing."""
import logging
from typing import List, Any, Optional
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CeleryOptimizer:
    """Optimizations for Celery task processing."""

    @staticmethod
    def configure_optimizations(app: Celery):
        """Apply performance optimizations to Celery app."""
        
        # Worker pool optimizations
        app.conf.update(
            worker_prefetch_multiplier=4,
            worker_max_tasks_per_child=1000,
            task_acks_late=True,
            task_reject_on_worker_lost=True,
            task_compression='gzip',
            task_serializer='json',
            accept_content=['json', 'msgpack'],
            result_compression='gzip',
            result_serializer='json',
            result_expires=3600,
            task_default_rate_limit='100/s',
        )
        
        logger.info("Celery optimizations applied")
    
    @staticmethod
    def batch_tasks(task_func, items: List[Any], batch_size: int = 100):
        """Process items in batches to reduce overhead."""
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            task_func.delay(batch)
            logger.debug(f"Queued batch {i//batch_size + 1} with {len(batch)} items")
    
    @staticmethod
    def chunked_task(items: List[Any], chunk_size: int = 50):
        """Generator that yields chunks for processing."""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    @staticmethod
    def rate_limit_key(key: str, max_requests: int = 100, window: int = 60) -> bool:
        """Rate limit based on cache key."""
        cache_key = f"ratelimit:{key}"
        current = cache.get(cache_key, 0)
        
        if current >= max_requests:
            return False
        
        cache.set(cache_key, current + 1, window)
        return True


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task start for monitoring."""
    logger.debug(f"Task {task.name}[{task_id}] started")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    """Log task completion and update metrics."""
    if state == 'SUCCESS':
        logger.debug(f"Task {task.name}[{task_id}] completed successfully")
    elif state == 'FAILURE':
        logger.error(f"Task {task.name}[{task_id}] failed")
    
    # Update metrics in cache
    metrics_key = f"celery:metrics:{task.name}"
    metrics = cache.get(metrics_key, {
        'total': 0,
        'success': 0,
        'failure': 0,
        'avg_runtime': 0,
    })
    
    metrics['total'] += 1
    if state == 'SUCCESS':
        metrics['success'] += 1
    else:
        metrics['failure'] += 1
    
    cache.set(metrics_key, metrics, 86400)  # 24 hours


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failures with retry logic."""
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}")
    
    # Increment failure count
    failure_key = f"celery:failures:{sender.name}"
    failures = cache.get(failure_key, 0)
    cache.set(failure_key, failures + 1, 3600)
    
    # Alert if too many failures
    if failures + 1 >= 10:
        logger.critical(
            f"Task {sender.name} has {failures + 1} failures in the last hour. "
            f"Check task health."
        )


class BatchProcessor:
    """Utility for batch processing large datasets."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.buffer = []
    
    def add(self, item: Any):
        """Add item to buffer."""
        self.buffer.append(item)
        if len(self.buffer) >= self.batch_size:
            return self.flush()
        return None
    
    def flush(self) -> List[Any]:
        """Return and clear buffer."""
        batch = self.buffer[:self.batch_size]
        self.buffer = self.buffer[self.batch_size:]
        return batch
    
    def __iter__(self):
        """Yield remaining items."""
        while self.buffer:
            batch = self.flush()
            if batch:
                yield batch
