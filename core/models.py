"""
Core models. Keep it flat and simple — no deep nesting.
Every model maps to a clear business concept.
"""
import uuid
import secrets
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def active(self):
        """Explicitly filter for active records (same as default)."""
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Filter for soft-deleted records only."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteAllManager(models.Manager):
    """Manager that includes all records (including soft-deleted)."""
    def get_queryset(self):
        return super().get_queryset()


class EmailVerification(models.Model):
    """Email verification codes for user registration."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_verification")
    code_hash = models.CharField(max_length=64)  # SHA-256 hash
    salt = models.CharField(max_length=32)  # Per-code salt
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    MAX_ATTEMPTS = 5

    class Meta:
        indexes = [models.Index(fields=["created_at"])]

    def set_code(self, code: str):
        """Hash and store the verification code with a unique salt."""
        self.salt = secrets.token_hex(16)
        self.code_hash = hashlib.sha256(
            f"{self.salt}{code}".encode()
        ).hexdigest()

    def verify_code(self, code: str) -> bool:
        """Verify the code against the stored hash using constant-time comparison."""
        expected = hashlib.sha256(
            f"{self.salt}{code}".encode()
        ).hexdigest()
        return secrets.compare_digest(self.code_hash, expected)

    def is_expired(self):
        """Code expires after 15 minutes."""
        return (timezone.now() - self.created_at).total_seconds() > 900

    def is_locked(self):
        """Check if too many failed attempts have been made."""
        return self.attempts >= self.MAX_ATTEMPTS

    def record_attempt(self):
        """Increment failed attempt counter."""
        self.attempts += 1
        self.save(update_fields=["attempts"])
    
    def __str__(self):
        return f"Verification for {self.user.email} - {'Verified' if self.is_verified else 'Pending'}"


class PasswordResetCode(models.Model):
    """6-digit password reset codes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes")
    code_hash = models.CharField(max_length=64)  # SHA-256 hash
    salt = models.CharField(max_length=32)  # Per-code salt
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"])]
    
    def set_code(self, code: str):
        """Hash and store the reset code with a unique salt."""
        self.salt = secrets.token_hex(16)
        self.code_hash = hashlib.sha256(
            f"{self.salt}{code}".encode()
        ).hexdigest()

    def verify_code(self, code: str) -> bool:
        """Verify the code against the stored hash using constant-time comparison."""
        expected = hashlib.sha256(
            f"{self.salt}{code}".encode()
        ).hexdigest()
        return secrets.compare_digest(self.code_hash, expected)

    def is_expired(self):
        """Code expires after 15 minutes."""
        return (timezone.now() - self.created_at).total_seconds() > 900

    def clean_expired_codes(self):
        """Delete old used or expired codes for this user."""
        self.__class__.objects.filter(
            user=self.user,
            created_at__lt=timezone.now() - timezone.timedelta(minutes=15)
        ).delete()
        self.__class__.objects.filter(
            user=self.user,
            is_used=True
        ).exclude(id=self.id).delete()

    def __str__(self):
        return f"Reset code for {self.user.email}"


class BusinessProfile(models.Model):
    """
    One profile per user. Stores business context the agent
    uses in every conversation — no need to re-fetch from docs.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business_profile")
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)  # e.g. "10-50"
    website = models.URLField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    # DEPRECATED: Use Goal model with FK to BusinessProfile instead
    goals = models.JSONField(default=list)
    # DEPRECATED: Use Metric model with FK to BusinessProfile instead
    key_metrics = models.JSONField(default=dict)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class Goal(models.Model):
    """
    Business goals as proper model (replaces JSONField abuse in BusinessProfile).
    Searchable, filterable, sortable.
    """
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_profile = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="goals_proper"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    target_date = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=0)  # Higher = more important
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["business_profile", "status"]),
            models.Index(fields=["business_profile", "target_date"]),
        ]

    def __str__(self):
        return self.title


class Metric(models.Model):
    """
    Business metrics as proper model (replaces JSONField abuse in BusinessProfile).
    Track numeric and text metrics with history support.
    """
    METRIC_TYPE_CHOICES = [
        ("number", "Number"),
        ("currency", "Currency"),
        ("percentage", "Percentage"),
        ("text", "Text"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_profile = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="metrics"
    )
    key = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)  # Display name
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES, default="number")
    value_numeric = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    value_text = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=50, blank=True)  # e.g., "USD", "users", "%"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["business_profile", "key"]),
        ]
        unique_together = ("business_profile", "key")

    def __str__(self):
        return f"{self.name}: {self.value_numeric or self.value_text}"


class UserMemory(models.Model):
    """
    Lightweight structured memory. NOT a vector DB.
    Agent writes key facts here; retrieves them by category.
    Think of it as a smart notepad the agent maintains.
    """
    CATEGORY_CHOICES = [
        ("preference", "User Preference"),
        ("decision", "Business Decision"),
        ("context", "Important Context"),
        ("fact", "Key Fact"),
        ("followup", "Follow-up Item"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memories")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="fact")
    key = models.CharField(max_length=100, db_index=True)         # e.g. "preferred_report_format"
    value = models.TextField()                     # e.g. "bullet points with numbers"
    source_conversation = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "key")          # one value per key per user
        indexes = [models.Index(fields=["user", "category"])]

    def __str__(self):
        return f"{self.user.username} | {self.key}: {self.value[:50]}"


class Document(models.Model):
    """
    Uploaded documents (PDF, DOCX, TXT).
    We store a summary + chunks — never re-read the full file.
    Supports soft delete - records are marked deleted, not actually removed.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/", null=True, blank=True)
    file_type = models.CharField(max_length=10)    # pdf, docx, txt
    summary = models.TextField(blank=True)         # AI-generated summary (stored once)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    page_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_documents")

    # Managers
    objects = SoftDeleteManager()  # Default - excludes soft-deleted
    all_objects = SoftDeleteAllManager()  # Includes all

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
            models.Index(fields=["user", "file_type"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    def soft_delete(self, user=None):
        """Mark record as deleted without removing from database."""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self):
        """Actually remove from database (use with caution)."""
        super().delete()


class DocumentChunk(models.Model):
    """
    Pre-chunked document sections. Supports both keyword search
    and semantic vector search (pgvector placeholder).
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    content = models.TextField()
    page_number = models.IntegerField(default=0)
    keywords = models.JSONField(default=list)      # extracted keywords for fast lookup
    
    # Semantic search - vector embedding (pgvector placeholder)
    # Stores embedding vector as JSON array for cosine similarity search
    # In production, use pgvector extension with dedicated VectorField
    embedding = models.JSONField(
        default=list,
        blank=True,
        help_text="Vector embedding for semantic search [768-dim or 1536-dim]"
    )
    embedding_model = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Model used to generate embedding (e.g., 'text-embedding-3-small')"
    )
    embedding_generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
            models.Index(fields=["keywords"]),
            models.Index(fields=["embedding_model"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
    
    def has_embedding(self) -> bool:
        """Check if this chunk has a valid embedding vector."""
        return len(self.embedding) > 0
    
    def cosine_similarity(self, other_embedding: list) -> float:
        """Calculate cosine similarity with another embedding vector."""
        if not self.has_embedding() or not other_embedding:
            return 0.0
        
        import math
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(self.embedding, other_embedding))
        
        # Calculate magnitudes
        mag_a = math.sqrt(sum(x * x for x in self.embedding))
        mag_b = math.sqrt(sum(x * x for x in other_embedding))
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot_product / (mag_a * mag_b)


class Conversation(models.Model):
    """One conversation session. Supports soft delete."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_conversations")

    # Managers
    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"Conv {self.id} — {self.user.username}"

    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self):
        super().delete()


class Message(models.Model):
    """Individual message in a conversation."""
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant"), ("tool", "Tool")]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_calls = models.JSONField(null=True, blank=True)   # what tools were called
    tool_results = models.JSONField(null=True, blank=True) # what tools returned
    model_used = models.CharField(max_length=50, blank=True) # gemini/groq/openrouter
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]


# =============================================================================
# TASK MANAGEMENT MODELS
# =============================================================================

class Task(models.Model):
    """
    Task management for business operations.
    Supports natural language creation, AI suggestions, team collaboration, and soft delete.
    """
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("done", "Done"),
        ("archived", "Archived"),
    ]
    
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_tasks")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")
    
    # Links to other entities
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="tasks")
    
    # Time tracking
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # Hierarchy
    is_subtask = models.BooleanField(default=False)
    parent_task = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_tasks")

    # Managers
    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Core lookups
            models.Index(fields=["user", "status", "-created_at"]),
            models.Index(fields=["user", "priority", "-created_at"]),
            # Assignment queries
            models.Index(fields=["assignee", "status", "-created_at"]),
            # Due date queries (for overdue detection)
            models.Index(fields=["due_date", "status"]),
            # Status-specific with priority for dashboard
            models.Index(fields=["status", "priority", "-created_at"]),
            # Soft delete index
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self):
        super().delete()


class TaskTag(models.Model):
    """Tags for organizing tasks."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="tags")
    tag = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("task", "tag")
    
    def __str__(self):
        return self.tag


class TaskComment(models.Model):
    """Comments on tasks for collaboration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class TaskActivity(models.Model):
    """Audit trail of task changes."""
    ACTIVITY_TYPES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("status_changed", "Status Changed"),
        ("priority_changed", "Priority Changed"),
        ("assigned", "Assigned"),
        ("completed", "Completed"),
        ("commented", "Commented"),
        ("archived", "Archived"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.activity_type} on {self.task.title}"


class TaskAttachment(models.Model):
    """Links between tasks and documents."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    attached_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("task", "document")
    
    def __str__(self):
        return f"{self.document.title} attached to {self.task.title}"


class TaskAISuggestion(models.Model):
    """AI-suggested tasks extracted from conversations or documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_suggestions")
    
    # Suggested content
    suggested_title = models.CharField(max_length=255)
    suggested_description = models.TextField(blank=True)
    suggested_priority = models.CharField(max_length=20, choices=Task.PRIORITY_CHOICES, default="medium")
    suggested_due_date = models.DateTimeField(null=True, blank=True)
    
    # Source tracking
    source_type = models.CharField(max_length=100)  # chat, document, email_pattern
    source_id = models.CharField(max_length=255, blank=True)  # conversation_id, document_id
    source_content = models.TextField(blank=True)  # Original text that triggered suggestion
    
    # AI metadata
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # User decision
    was_accepted = models.BooleanField(null=True, blank=True)
    created_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_suggestion")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"AI Suggestion: {self.suggested_title} ({'Accepted' if self.was_accepted else 'Pending'})"


class Notification(models.Model):
    """In-app notifications for users."""
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    action_url = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"], name="notification_unread_idx")
        ]

    def __str__(self):
        return f"{self.priority}: {self.message[:50]}"


class AuditLog(models.Model):
    """Comprehensive security audit log for compliance and forensics."""
    
    EVENT_TYPES = [
        # Authentication events
        ("login", "User Login"),
        ("logout", "User Logout"),
        ("login_failed", "Login Failed"),
        ("token_refresh", "Token Refresh"),
        ("password_change", "Password Change"),
        ("password_reset", "Password Reset"),
        ("mfa_enabled", "MFA Enabled"),
        ("mfa_disabled", "MFA Disabled"),
        ("session_revoked", "Session Revoked"),
        ("session_revoked_all", "All Sessions Revoked"),
        
        # Document events
        ("document_upload", "Document Upload"),
        ("document_download", "Document Download"),
        ("document_delete", "Document Delete"),
        ("document_view", "Document View"),
        
        # Task events
        ("task_create", "Task Create"),
        ("task_update", "Task Update"),
        ("task_delete", "Task Delete"),
        ("task_complete", "Task Complete"),
        ("task_reopen", "Task Reopen"),
        
        # AI events
        ("ai_prompt", "AI Prompt"),
        ("ai_response", "AI Response"),
        ("ai_suggestion_accepted", "AI Suggestion Accepted"),
        ("ai_suggestion_rejected", "AI Suggestion Rejected"),
        
        # Permission events
        ("permission_grant", "Permission Grant"),
        ("permission_revoke", "Permission Revoke"),
        ("role_change", "Role Change"),
        
        # Data events
        ("export", "Data Export"),
        ("bulk_delete", "Bulk Delete"),
        ("settings_change", "Settings Change"),
    ]
    
    SEVERITY_LEVELS = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="audit_logs"
    )
    
    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default="info")
    description = models.TextField()
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Resource tracking
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Before/after for changes
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="audit_user_created_idx"),
            models.Index(fields=["event_type", "-created_at"], name="audit_event_created_idx"),
            models.Index(fields=["severity", "-created_at"], name="audit_severity_created_idx"),
        ]
    
    def __str__(self):
        return f"{self.event_type} by {self.user.username if self.user else 'system'} at {self.created_at}"


class WorkspaceContext(models.Model):
    """Business context and AI memory persistence per workspace."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workspace_contexts")
    
    # Workspace identification
    workspace_id = models.CharField(max_length=100, db_index=True, help_text="Unique workspace identifier")
    workspace_name = models.CharField(max_length=200, blank=True)
    
    # Business context - company/business specific information
    business_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Business-specific context: company info, industry, tone, etc."
    )
    
    # AI Memory - persistent facts learned about the user/workspace
    ai_memory = models.JSONField(
        default=list,
        blank=True,
        help_text="Persistent AI memory: facts, preferences, learned context"
    )
    
    # Conversation summaries for long-term context
    conversation_summaries = models.JSONField(
        default=list,
        blank=True,
        help_text="Summaries of past conversations for context"
    )
    
    # Settings per workspace
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Workspace-specific preferences (tone, response style, etc.)"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-last_accessed"]
        indexes = [
            models.Index(fields=["user", "workspace_id"], name="workspace_ctx_user_idx"),
            models.Index(fields=["workspace_id"], name="workspace_ctx_id_idx"),
        ]
        unique_together = ["user", "workspace_id"]
    
    def __str__(self):
        return f"{self.workspace_name or self.workspace_id} context for {self.user.username}"
    
    def add_memory(self, memory_type: str, content: str, source_conversation_id: str = None):
        """Add a new memory entry."""
        memory_entry = {
            "type": memory_type,
            "content": content,
            "created_at": timezone.now().isoformat(),
            "source": source_conversation_id,
        }
        self.ai_memory.append(memory_entry)
        self.save(update_fields=["ai_memory"])
        return memory_entry
    
    def add_conversation_summary(self, conversation_id: str, summary: str, topics: list = None):
        """Add a conversation summary for long-term context."""
        summary_entry = {
            "conversation_id": conversation_id,
            "summary": summary,
            "topics": topics or [],
            "created_at": timezone.now().isoformat(),
        }
        # Keep only last 20 summaries to prevent bloat
        self.conversation_summaries = self.conversation_summaries[-19:] + [summary_entry]
        self.save(update_fields=["conversation_summaries"])
        return summary_entry
    
    def update_business_context(self, **kwargs):
        """Update business context fields."""
        self.business_context.update(kwargs)
        self.save(update_fields=["business_context"])
    
    def get_context_for_prompt(self) -> dict:
        """Get formatted context for AI prompt injection."""
        recent_memories = self.ai_memory[-10:]  # Last 10 memories
        recent_summaries = self.conversation_summaries[-3:]  # Last 3 conversation summaries
        
        return {
            "business_context": self.business_context,
            "recent_memories": recent_memories,
            "conversation_history": recent_summaries,
            "preferences": self.preferences,
        }


class DocumentVersion(models.Model):
    """
    Track document versions with diff support.
    Each version stores the full file and metadata about changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    
    # Version metadata
    file = models.FileField(upload_to=document_file_path)
    file_size = models.BigIntegerField(default=0)
    file_hash = models.CharField(max_length=64, blank=True)  # SHA-256 hash
    
    # Change tracking
    change_summary = models.TextField(blank=True, default="")
    change_type = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("edited", "Edited"),
            ("replaced", "Replaced"),
            ("minor", "Minor Update"),
        ],
        default="replaced"
    )
    
    # Text diff (for text-based documents)
    previous_text = models.TextField(blank=True, default="")
    text_diff = models.TextField(blank=True, default="")  # Unified diff format
    
    # Who made the change
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="document_versions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-version_number"]
        unique_together = ["document", "version_number"]
        indexes = [
            models.Index(fields=["document", "version_number"]),
            models.Index(fields=["file_hash"]),
        ]
    
    def __str__(self):
        return f"v{self.version_number} of {self.document.title}"
    
    @property
    def is_latest(self) -> bool:
        """Check if this is the latest version of the document."""
        latest = DocumentVersion.objects.filter(
            document=self.document
        ).order_by("-version_number").first()
        return latest == self if latest else True
    
    @property
    def previous_version(self) -> Optional["DocumentVersion"]:
        """Get the previous version of this document."""
        if self.version_number <= 1:
            return None
        try:
            return DocumentVersion.objects.get(
                document=self.document,
                version_number=self.version_number - 1
            )
        except DocumentVersion.DoesNotExist:
            return None


class TaskComment(models.Model):
    """
    Comments on tasks for collaboration.
    Supports @mentions and threaded replies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    
    # Mentions: List of user IDs mentioned in the comment
    mentions = models.JSONField(default=list, blank=True)
    
    # Threading support
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    
    # Editing tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
            models.Index(fields=["user"]),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title[:30]}"


class TaskSubtask(models.Model):
    """
    Subtasks for breaking down larger tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=[
            ("todo", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
        default="todo"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_subtasks"
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["created_at"]
    
    def __str__(self):
        return f"Subtask: {self.title[:50]}"


class TimeEntry(models.Model):
    """
    Time tracking entries for tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_entries")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Time tracking
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Optional description of what was done
    description = models.TextField(blank=True, default="")
    
    # For manual time entry
    is_manual = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["task", "start_time"]),
            models.Index(fields=["user", "start_time"]),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title[:30]} ({self.duration_minutes}m)"
    
    def save(self, *args, **kwargs):
        # Calculate duration if end_time is set
        if self.end_time and self.start_time and not self.duration_minutes:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)


class Notification(models.Model):
    """
    Real-time notifications for task assignments, mentions, due dates.
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_mentioned', 'Task Mention'),
        ('due_date_approaching', 'Due Date Approaching'),
        ('due_date_overdue', 'Task Overdue'),
        ('task_completed', 'Task Completed'),
        ('comment_reply', 'Comment Reply'),
        ('document_shared', 'Document Shared'),
        ('system', 'System Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    
    # Notification content
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Link to related objects
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(TaskComment, on_delete=models.CASCADE, null=True, blank=True)
    
    # Actor who triggered the notification (if applicable)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="triggered_notifications")
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # WebSocket delivery tracking
    websocket_delivered = models.BooleanField(default=False)
    websocket_delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Email/push notification tracking
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.title[:50]}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """
    User preferences for notification settings.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_preferences")
    
    # In-app notifications
    task_assigned_in_app = models.BooleanField(default=True)
    task_mentioned_in_app = models.BooleanField(default=True)
    due_date_approaching_in_app = models.BooleanField(default=True)
    due_date_overdue_in_app = models.BooleanField(default=True)
    comment_reply_in_app = models.BooleanField(default=True)
    
    # Email notifications
    task_assigned_email = models.BooleanField(default=True)
    task_mentioned_email = models.BooleanField(default=True)
    due_date_approaching_email = models.BooleanField(default=True)
    due_date_overdue_email = models.BooleanField(default=True)
    
    # Due date notification timing (hours before due date)
    due_date_warning_hours = models.PositiveIntegerField(default=24)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class Workspace(models.Model):
    """
    Workspace for organizing users and resources with role-based permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_workspaces")
    
    # Settings
    is_public = models.BooleanField(default=False)
    allow_invite_links = models.BooleanField(default=True)
    default_member_role = models.CharField(
        max_length=20,
        choices=[
            ('viewer', 'Viewer'),
            ('member', 'Member'),
        ],
        default='member'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        return self.members.count()


class WorkspaceMember(models.Model):
    """
    Workspace membership with role-based permissions.
    Roles: owner > admin > member > viewer
    """
    ROLES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    
    # Invite tracking
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_members"
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['workspace', 'user']
        ordering = ['-role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.workspace.name}"
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        role_permissions = {
            'owner': ['create', 'read', 'update', 'delete', 'manage_members', 'manage_settings', 'manage_roles'],
            'admin': ['create', 'read', 'update', 'delete', 'manage_members'],
            'member': ['create', 'read', 'update', 'delete_own'],
            'viewer': ['read'],
        }
        return permission in role_permissions.get(self.role, [])
    
    def can_manage_member(self, target_role: str) -> bool:
        """Check if this member can manage another member with target_role."""
        hierarchy = {'owner': 4, 'admin': 3, 'member': 2, 'viewer': 1}
        return hierarchy.get(self.role, 0) > hierarchy.get(target_role, 0)


class ResourcePermission(models.Model):
    """
    Granular permissions for specific resources (tasks, documents, etc.)
    """
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('share', 'Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Resource being protected (generic foreign key pattern)
    resource_type = models.CharField(max_length=50)  # 'task', 'document', 'conversation'
    resource_id = models.UUIDField()
    
    # Who has access
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="resource_permissions"
    )
    workspace_member = models.ForeignKey(
        WorkspaceMember,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="resource_permissions"
    )
    
    permission = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="granted_permissions")
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['resource_type', 'resource_id', 'user', 'permission']
    
    def __str__(self):
        target = self.user.username if self.user else f"{self.workspace_member.role} in {self.workspace_member.workspace.name}"
        return f"{self.permission} on {self.resource_type}:{self.resource_id} for {target}"


class APIToken(models.Model):
    """
    API tokens for third-party integrations (Zapier, Make, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")
    name = models.CharField(max_length=255, help_text="e.g., 'Zapier Production'")
    token_hash = models.CharField(max_length=255, unique=True)
    
    # Scopes for granular permissions
    scopes = models.JSONField(default=list, help_text="['tasks:read', 'tasks:write', 'documents:read']")
    
    # Rate limiting per token
    rate_limit = models.PositiveIntegerField(default=1000, help_text="Requests per hour")
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.now():
            return False
        return True


class Webhook(models.Model):
    """
    Webhook subscriptions for event-driven integrations.
    """
    EVENT_TYPES = [
        ('task.created', 'Task Created'),
        ('task.updated', 'Task Updated'),
        ('task.deleted', 'Task Deleted'),
        ('task.completed', 'Task Completed'),
        ('document.created', 'Document Created'),
        ('document.updated', 'Document Updated'),
        ('comment.created', 'Comment Created'),
        ('member.invited', 'Member Invited'),
        ('member.joined', 'Member Joined'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhooks")
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="webhooks"
    )
    
    # Configuration
    name = models.CharField(max_length=255)
    url = models.URLField()
    events = models.JSONField(default=list, help_text="List of event types to subscribe to")
    
    # Security
    secret = models.CharField(max_length=255, help_text="Secret for HMAC signature")
    headers = models.JSONField(default=dict, blank=True, help_text="Custom headers")
    
    # Delivery settings
    is_active = models.BooleanField(default=True)
    retry_count = models.PositiveIntegerField(default=3)
    timeout_seconds = models.PositiveIntegerField(default=30)
    
    # Delivery tracking
    last_delivered_at = models.DateTimeField(null=True, blank=True)
    last_status_code = models.PositiveIntegerField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} -> {self.url}"


class WebhookDelivery(models.Model):
    """
    Log of webhook delivery attempts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name="deliveries")
    
    # Delivery details
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    
    # Attempt tracking
    attempt_number = models.PositiveIntegerField(default=1)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'
    RETRYING = 'retrying'
    
    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (PENDING, 'Pending'),
        (RETRYING, 'Retrying'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['webhook', '-started_at']),
            models.Index(fields=['event_type', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} ({self.status})"


class ConversationMemory(models.Model):
    """Per-conversation memory for maintaining context within a chat session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.OneToOneField(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name="memory"
    )
    
    # Extracted facts and entities from the conversation
    extracted_facts = models.JSONField(default=list, blank=True)
    user_intents = models.JSONField(default=list, blank=True)
    
    # Running summary of the conversation
    running_summary = models.TextField(blank=True)
    
    # Key topics discussed
    topics = models.JSONField(default=list, blank=True)
    
    # Last updated
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"Memory for conversation {self.conversation.id}"
    
    def add_fact(self, fact: str, confidence: float = 1.0):
        """Add an extracted fact."""
        self.extracted_facts.append({
            "fact": fact,
            "confidence": confidence,
            "added_at": timezone.now().isoformat(),
        })
        self.save(update_fields=["extracted_facts", "updated_at"])
    
    def update_summary(self, summary: str):
        """Update the running conversation summary."""
        self.running_summary = summary
        self.save(update_fields=["running_summary", "updated_at"])
