"""Analytics Models - User engagement, feature usage, AI metrics."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserActivity(models.Model):
    """Track user interactions and engagement."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    workspace = models.ForeignKey("Workspace", on_delete=models.CASCADE, related_name="activities", null=True, blank=True)
    
    # Activity details
    event_type = models.CharField(max_length=50)  # task_created, document_uploaded, chat_message, etc.
    feature = models.CharField(max_length=50)  # tasks, documents, chat, kanban, etc.
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["workspace", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["feature", "created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name_plural = "User Activities"


class FeatureUsage(models.Model):
    """Aggregate feature usage statistics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feature_usage")
    workspace = models.ForeignKey("Workspace", on_delete=models.CASCADE, related_name="feature_usage", null=True, blank=True)
    
    # Feature stats
    feature = models.CharField(max_length=50)
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(auto_now=True)
    
    # Daily aggregation
    date = models.DateField()
    
    class Meta:
        unique_together = [["user", "workspace", "feature", "date"]]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["workspace", "date"]),
            models.Index(fields=["feature", "date"]),
        ]


class AIMetrics(models.Model):
    """Track AI model usage and costs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_metrics")
    workspace = models.ForeignKey("Workspace", on_delete=models.CASCADE, related_name="ai_metrics", null=True, blank=True)
    
    # Request details
    model = models.CharField(max_length=100)  # gpt-4, gpt-3.5-turbo, etc.
    operation = models.CharField(max_length=50)  # chat, task_generation, summarization, etc.
    
    # Token usage
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    
    # Cost (in USD, estimated)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance
    response_time_ms = models.PositiveIntegerField()
    
    # Result
    success = models.BooleanField(default=True)
    error_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["workspace", "created_at"]),
            models.Index(fields=["model", "created_at"]),
            models.Index(fields=["operation", "created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name_plural = "AI Metrics"


class SessionAnalytics(models.Model):
    """Track user sessions for retention analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions_analytics")
    
    # Session details
    session_id = models.CharField(max_length=255, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    
    # Engagement
    page_views = models.PositiveIntegerField(default=0)
    actions_count = models.PositiveIntegerField(default=0)
    
    # Device/Location
    device_type = models.CharField(max_length=20, default="unknown")  # mobile, tablet, desktop
    user_agent = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["user", "started_at"]),
            models.Index(fields=["started_at"]),
        ]


class RetentionSnapshot(models.Model):
    """Daily retention metrics snapshot."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    
    # User counts
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    returning_users = models.PositiveIntegerField(default=0)
    
    # Retention cohorts
    day_1_retention = models.FloatField(default=0)  # % of new users who returned next day
    day_7_retention = models.FloatField(default=0)
    day_30_retention = models.FloatField(default=0)
    
    # Workspace metrics
    total_workspaces = models.PositiveIntegerField(default=0)
    active_workspaces = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)


class AnalyticsExport(models.Model):
    """Scheduled/requested analytics exports."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="analytics_exports")
    workspace = models.ForeignKey("Workspace", on_delete=models.CASCADE, related_name="analytics_exports", null=True, blank=True)
    
    # Export details
    export_type = models.CharField(max_length=50)  # csv, json
    data_scope = models.CharField(max_length=50)  # user, workspace, admin
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, default="pending")  # pending, processing, completed, failed
    file_url = models.URLField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    
    # Schedule
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    
    # Privacy
    anonymized = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
