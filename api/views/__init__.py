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
    document_summary,
    document_status,
    delete_document,
    document_download,
    documents_status_summary,
    reprocess_document,
)

# User & Profile
from .profile_views import (
    get_user_info,
    update_username,
    update_password,
    business_profile,
)

# Authentication
from .auth_views import (
    register,
    login,
    logout,
    token_refresh,
    verify_email,
    resend_verification,
    forgot_password,
    verify_reset_code,
    reset_password,
)

# Tasks
from .task_views import (
    list_tasks,
    create_task,
    get_task,
    update_task,
    delete_task,
    complete_task,
    reopen_task,
    list_comments,
    create_comment,
    delete_comment,
    list_activities,
    task_dashboard,
    task_stats,
)

# Analytics
from .analytics_views import (
    get_analytics,
    get_user_engagement,
    get_ai_usage,
    get_workspace_analytics,
    get_admin_dashboard,
    get_retention_report,
    request_analytics_export,
    get_export_status,
    delete_analytics_data,
)

# Async
from .async_views import (
    async_process_document,
    async_bulk_task_update,
    async_job_status,
)

# Workspace
from .workspace_views import (
    get_workspace_context,
    update_business_context,
    add_memory,
    get_memories,
    delete_memory,
    add_conversation_summary,
    update_preferences,
    archive_workspace,
)

# AI Tasks
from .ai_task_views import (
    generate_tasks_from_chat,
    generate_tasks_from_document,
    get_pending_ai_tasks,
    accept_ai_task,
    reject_ai_task,
)

# Task Detail
from .task_detail_views import (
    get_task_details,
    add_comment,
    edit_comment,
    reply_to_comment,
    add_subtask,
    update_subtask,
    delete_subtask,
    start_timer,
    stop_timer,
    add_manual_time,
    delete_time_entry,
    get_active_timer,
)

# Webhooks
from .webhook_views import (
    list_webhooks,
    create_webhook,
    get_webhook,
    update_webhook,
    delete_webhook,
    test_webhook,
    list_deliveries,
    regenerate_secret,
    get_available_events,
)

# API Tokens
from .api_token_views import (
    list_api_tokens,
    create_api_token,
    revoke_api_token,
    zapier_triggers,
    zapier_actions,
    zapier_sample_data,
    integration_status,
)

# API Docs
from .api_docs_views import (
    get_openapi_spec,
    api_documentation,
    get_api_examples,
)

# Permissions
from .permission_views import (
    list_workspaces,
    create_workspace,
    get_workspace,
    update_workspace,
    delete_workspace,
    list_members,
    invite_member,
    update_member_role,
    remove_member,
    check_permission,
    check_resource_permission,
    grant_permission,
    revoke_permission,
)

# Semantic Search
from .semantic_search_views import (
    semantic_search,
    conversational_retrieval,
    generate_embeddings,
)

# Document Analysis
from .document_analysis_views import (
    analyze_document,
    auto_extract_tasks,
    get_document_insights,
)

# Smart Actions
from .smart_action_views import (
    smart_action_view,
)

# Document Versioning
from .document_version_views import (
    list_document_versions,
    get_version_diff,
    compare_versions,
    create_version,
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
    get_unread_count,
    mark_all_read,
    get_notification_preferences,
    update_notification_preferences,
)

# Session Management
from .session_views import (
    list_sessions,
    revoke_session,
    revoke_all_other_sessions,
)

# Misc (tags, health)
from .misc_views import (
    tags_list_create,
    tasks_by_tag,
    task_add_tag,
    task_remove_tag,
    ai_health,
)

__all__ = [
    # Health
    "health_check",
    "ai_health",
    # Auth
    "register",
    "login",
    "logout",
    "token_refresh",
    "verify_email",
    "resend_verification",
    "forgot_password",
    "verify_reset_code",
    "reset_password",
    # Tasks
    "list_tasks",
    "create_task",
    "get_task",
    "update_task",
    "delete_task",
    "complete_task",
    "reopen_task",
    "list_comments",
    "create_comment",
    "delete_comment",
    "list_activities",
    "task_dashboard",
    "task_stats",
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
    "document_summary",
    "document_status",
    "delete_document",
    "document_download",
    "documents_status_summary",
    "reprocess_document",
    # User & Profile
    "get_user_info",
    "update_username",
    "update_password",
    "business_profile",
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
    "get_unread_count",
    "mark_all_read",
    "get_notification_preferences",
    "update_notification_preferences",
    # Session Management
    "list_sessions",
    "revoke_session",
    "revoke_all_other_sessions",
    # Misc
    "tags_list_create",
    "tasks_by_tag",
    "task_add_tag",
    "task_remove_tag",
    # Analytics
    "get_analytics",
    "get_user_engagement",
    "get_ai_usage",
    "get_workspace_analytics",
    "get_admin_dashboard",
    "get_retention_report",
    "request_analytics_export",
    "get_export_status",
    "delete_analytics_data",
    # Async
    "async_process_document",
    "async_bulk_task_update",
    "async_job_status",
    # Workspace
    "get_workspace_context",
    "update_business_context",
    "add_memory",
    "get_memories",
    "delete_memory",
    "add_conversation_summary",
    "update_preferences",
    "archive_workspace",
    # AI Tasks
    "generate_tasks_from_chat",
    "generate_tasks_from_document",
    "get_pending_ai_tasks",
    "accept_ai_task",
    "reject_ai_task",
    # Task Detail
    "get_task_details",
    "add_comment",
    "edit_comment",
    "reply_to_comment",
    "add_subtask",
    "update_subtask",
    "delete_subtask",
    "start_timer",
    "stop_timer",
    "add_manual_time",
    "delete_time_entry",
    "get_active_timer",
    # Webhooks
    "list_webhooks",
    "create_webhook",
    "get_webhook",
    "update_webhook",
    "delete_webhook",
    "test_webhook",
    "list_deliveries",
    "regenerate_secret",
    "get_available_events",
    # API Tokens
    "list_api_tokens",
    "create_api_token",
    "revoke_api_token",
    "zapier_triggers",
    "zapier_actions",
    "zapier_sample_data",
    "integration_status",
    # API Docs
    "get_openapi_spec",
    "api_documentation",
    "get_api_examples",
    # Permissions
    "list_workspaces",
    "create_workspace",
    "get_workspace",
    "update_workspace",
    "delete_workspace",
    "list_members",
    "invite_member",
    "update_member_role",
    "remove_member",
    "check_permission",
    "check_resource_permission",
    "grant_permission",
    "revoke_permission",
    # Semantic Search
    "semantic_search",
    "conversational_retrieval",
    "generate_embeddings",
    # Document Analysis
    "analyze_document",
    "auto_extract_tasks",
    "get_document_insights",
    # Smart Actions
    "smart_action_view",
    # Document Versioning
    "list_document_versions",
    "get_version_diff",
    "compare_versions",
    "create_version",
]
