# API Views - Modular Structure
# Re-exports all views from submodules for backwards compatibility

# Chat & Conversations
from .chat_views import (
    health_check,
    chat,
    chat_stream,
    conversation_list,
    conversation_detail,
    export_conversation,
    delete_conversation,
)

# Documents
from .document_views import (
    document_list,
    upload_document,
    document_status,
    delete_document,
    document_summary,
    document_download,
    reindex_document,
)

# User & Profile
from .profile_views import (
    get_user_info,
    update_username,
    update_password,
    business_profile,
    business_analytics,
)

# Onboarding
from .onboarding_views import (
    onboarding_status,
    seed_demo_data,
    onboarding_complete,
    extract_tasks_from_text,
    accept_task_suggestion,
    reject_task_suggestion,
)

# Admin
from .admin_views import (
    admin_dashboard,
    admin_broadcast,
    admin_reindex_all,
)

# Notifications
from .notification_views import (
    get_notifications,
    mark_notification_read,
)

# Misc (tags, health)
from .misc_views import (
    tags_list_create,
    tasks_by_tag,
    task_add_tag,
    task_remove_tag,
)

__all__ = [
    # Health
    "health_check",
    # Chat
    "chat",
    "chat_stream",
    "conversation_list",
    "conversation_detail",
    "export_conversation",
    "delete_conversation",
    # Documents
    "document_list",
    "upload_document",
    "document_status",
    "delete_document",
    "document_summary",
    "document_download",
    "reindex_document",
    # User & Profile
    "get_user_info",
    "update_username",
    "update_password",
    "business_profile",
    "business_analytics",
    # Onboarding
    "onboarding_status",
    "seed_demo_data",
    "onboarding_complete",
    "extract_tasks_from_text",
    "accept_task_suggestion",
    "reject_task_suggestion",
    # Admin
    "admin_dashboard",
    "admin_broadcast",
    "admin_reindex_all",
    # Notifications
    "get_notifications",
    "mark_notification_read",
    # Misc
    "tags_list_create",
    "tasks_by_tag",
    "task_add_tag",
    "task_remove_tag",
]
