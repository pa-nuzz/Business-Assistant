"""
Core models. Keep it flat and simple — no deep nesting.
Every model maps to a clear business concept.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EmailVerification(models.Model):
    """Email verification codes for user registration."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_verification")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    MAX_ATTEMPTS = 5

    class Meta:
        indexes = [models.Index(fields=["code", "created_at"])]

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
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["code", "created_at"])]
    
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
    description = models.TextField(blank=True)
    goals = models.JSONField(default=list)          # ["increase revenue", "expand to EU"]
    key_metrics = models.JSONField(default=dict)    # {"monthly_revenue": 50000, "customers": 120}
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


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

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
            models.Index(fields=["user", "file_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class DocumentChunk(models.Model):
    """
    Pre-chunked document sections. Agent fetches relevant
    chunks by keyword search — no vector embeddings needed.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    content = models.TextField()
    page_number = models.IntegerField(default=0)
    keywords = models.JSONField(default=list)      # extracted keywords for fast lookup

    class Meta:
        ordering = ["chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
            models.Index(fields=["keywords"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class Conversation(models.Model):
    """One conversation session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]

    def __str__(self):
        return f"Conv {self.id} — {self.user.username}"


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


# =============================================================================
# TASK MANAGEMENT MODELS
# =============================================================================

class Task(models.Model):
    """
    Task management for business operations.
    Supports natural language creation, AI suggestions, and team collaboration.
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
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"


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
