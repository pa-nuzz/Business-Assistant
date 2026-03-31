from django.contrib import admin
from core.models import BusinessProfile, UserMemory, Document, DocumentChunk, Conversation, Message


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "company_name", "industry", "updated_at"]
    search_fields = ["user__username", "company_name"]


@admin.register(UserMemory)
class UserMemoryAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "key", "updated_at"]
    list_filter = ["category"]
    search_fields = ["user__username", "key", "value"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "file_type", "status", "page_count", "created_at"]
    list_filter = ["status", "file_type"]
    search_fields = ["title", "user__username"]
    readonly_fields = ["summary"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "chunk_index", "page_number"]
    list_filter = ["document"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "updated_at"]
    search_fields = ["user__username", "title"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "role", "model_used", "created_at"]
    list_filter = ["role", "model_used"]
