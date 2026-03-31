"""
Core models. Keep it flat and simple — no deep nesting.
Every model maps to a clear business concept.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


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
    key = models.CharField(max_length=100)         # e.g. "preferred_report_format"
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
        indexes = [models.Index(fields=["document", "chunk_index"])]

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
