# API v1 URL Configuration
from django.urls import path
from api import views
from api.auth_views import (
    register, login, logout, verify_email, resend_verification,
    forgot_password, verify_reset_code, reset_password, token_refresh
)
from api.views import *  # Import all modular views
from api.views.analytics_views import (
    get_analytics, get_user_engagement, get_ai_usage,
    get_workspace_analytics, get_admin_dashboard, get_retention_report,
    request_analytics_export, get_export_status, delete_analytics_data
)
from api.task_views import (
    list_tasks, create_task, get_task, update_task, delete_task,
    complete_task, reopen_task, list_comments, create_comment, delete_comment,
    list_activities, task_dashboard, task_stats
)
from api.views.async_views import (
    async_process_document, async_bulk_task_update, async_job_status
)
from api.views.workspace_views import (
    list_workspaces, get_workspace_context, update_business_context,
    add_memory, get_memories, delete_memory, add_conversation_summary,
    update_preferences, archive_workspace
)
from api.views.ai_task_views import (
    generate_tasks_from_chat, generate_tasks_from_document,
    get_pending_ai_tasks, accept_ai_task, reject_ai_task
)
from api.views.task_detail_views import (
    get_task_details, add_comment, edit_comment, reply_to_comment,
    add_subtask, update_subtask, delete_subtask,
    start_timer, stop_timer, add_manual_time, delete_time_entry, get_active_timer
)
from api.views.notification_views import (
    get_notifications, get_unread_count, mark_notification_read,
    mark_all_read, get_notification_preferences, update_notification_preferences
)
from api.views.webhook_views import (
    list_webhooks, create_webhook, get_webhook, update_webhook, delete_webhook,
    test_webhook, list_deliveries, regenerate_secret, get_available_events
)
from api.views.api_token_views import (
    list_api_tokens, create_api_token, revoke_api_token,
    zapier_triggers, zapier_actions, zapier_sample_data, integration_status
)
from api.views.api_docs_views import (
    get_openapi_spec, api_documentation, get_api_examples
)
from api.views.permission_views import (
    list_workspaces, create_workspace, get_workspace, update_workspace, delete_workspace,
    list_members, invite_member, update_member_role, remove_member,
    check_permission, check_resource_permission, grant_permission, revoke_permission
)
from api.views.semantic_search_views import (
    semantic_search, conversational_retrieval, generate_embeddings
)
from api.views.document_analysis_views import (
    analyze_document, auto_extract_tasks, get_document_insights
)
from api.views.document_version_views import (
    list_document_versions, get_version_diff, compare_versions, create_version
)

app_name = "api_v1"

urlpatterns = [
    # Health
    path("health/", views.health_check, name="health-check"),

    # Auth (Premium Auth System with JWT + httpOnly cookies)
    path("auth/register/", register, name="register"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("auth/token/refresh/", token_refresh, name="token-refresh"),
    path("auth/verify-email/", verify_email, name="verify-email"),
    path("auth/resend-verification/", resend_verification, name="resend-verification"),
    path("auth/forgot-password/", forgot_password, name="forgot-password"),
    path("auth/verify-reset-code/", verify_reset_code, name="verify-reset-code"),
    path("auth/reset-password/", reset_password, name="reset-password"),

    # Chat
    path("chat/", views.chat, name="chat"),
    path("chat/stream/", views.chat_stream, name="chat-stream"),
    path("conversations/", views.conversation_list, name="conversation-list"),
    path("conversations/<uuid:conversation_id>/", views.conversation_detail, name="conversation-detail"),
    path("conversations/<uuid:conversation_id>/export/", views.export_conversation, name="conversation-export"),
    path("conversations/<uuid:conversation_id>/delete/", views.delete_conversation, name="delete-conversation"),

    # Documents
    path("documents/", views.document_list, name="document-list"),
    path("documents/upload/", views.upload_document, name="upload-document"),
    path("documents/<uuid:doc_id>/status/", views.document_status, name="document-status"),
    path("documents/<uuid:doc_id>/delete/", views.delete_document, name="document-delete"),
    path("documents/<uuid:doc_id>/download/", views.document_download, name="document-download"),

    # Business Profile
    path("profile/", views.business_profile, name="business-profile"),

    # User Management
    path("user/update-username/", views.update_username, name="update-username"),
    path("user/update-password/", views.update_password, name="update-password"),
    path("user/info/", views.get_user_info, name="user-info"),
    
    # Session Management (Security)
    path("user/sessions/", views.list_sessions, name="list-sessions"),
    path("user/sessions/revoke/", views.revoke_session, name="revoke-session"),
    path("user/sessions/revoke-all/", views.revoke_all_other_sessions, name="revoke-all-sessions"),

    # Task Management
    path("tasks/", list_tasks, name="task-list"),
    path("tasks/create/", create_task, name="task-create"),
    path("tasks/dashboard/", task_dashboard, name="task-dashboard"),
    path("tasks/stats/", task_stats, name="task-stats"),
    path("tasks/<uuid:task_id>/", get_task, name="task-detail"),
    path("tasks/<uuid:task_id>/update/", update_task, name="task-update"),
    path("tasks/<uuid:task_id>/delete/", delete_task, name="task-delete"),
    path("tasks/<uuid:task_id>/complete/", complete_task, name="task-complete"),
    path("tasks/<uuid:task_id>/reopen/", reopen_task, name="task-reopen"),
    path("tasks/<uuid:task_id>/comments/", list_comments, name="task-comments"),
    path("tasks/<uuid:task_id>/comments/create/", create_comment, name="task-comment-create"),
    path("tasks/<uuid:task_id>/comments/<uuid:comment_id>/delete/", delete_comment, name="task-comment-delete"),
    path("tasks/<uuid:task_id>/activities/", list_activities, name="task-activities"),

    # Task Detail Panel (Comments, Subtasks, Time Tracking)
    path("tasks/<uuid:task_id>/details/", get_task_details, name="task-details"),
    path("tasks/<uuid:task_id>/comments/add/", add_comment, name="task-comment-add"),
    path("tasks/comments/<uuid:comment_id>/edit/", edit_comment, name="task-comment-edit"),
    path("tasks/<uuid:task_id>/comments/<uuid:comment_id>/reply/", reply_to_comment, name="task-comment-reply"),
    path("tasks/<uuid:task_id>/subtasks/add/", add_subtask, name="task-subtask-add"),
    path("tasks/subtasks/<uuid:subtask_id>/update/", update_subtask, name="task-subtask-update"),
    path("tasks/subtasks/<uuid:subtask_id>/delete/", delete_subtask, name="task-subtask-delete"),
    path("tasks/<uuid:task_id>/timer/start/", start_timer, name="task-timer-start"),
    path("tasks/timer/<uuid:entry_id>/stop/", stop_timer, name="task-timer-stop"),
    path("tasks/<uuid:task_id>/time/add/", add_manual_time, name="task-time-add"),
    path("tasks/time/<uuid:entry_id>/delete/", delete_time_entry, name="task-time-delete"),
    path("tasks/timer/active/", get_active_timer, name="task-timer-active"),

    # AI Task Extraction
    path("tasks/extract/", views.extract_tasks_from_text, name="task-extract"),
    path("tasks/suggestions/<uuid:suggestion_id>/accept/", views.accept_task_suggestion, name="task-suggestion-accept"),
    path("tasks/suggestions/<uuid:suggestion_id>/reject/", views.reject_task_suggestion, name="task-suggestion-reject"),

    # Tags API
    path("tags/", views.tags_list_create, name="tags-list-create"),
    path("tags/<str:tag_name>/tasks/", views.tasks_by_tag, name="tasks-by-tag"),
    path("tasks/<uuid:task_id>/tags/add/", views.task_add_tag, name="task-add-tag"),
    path("tasks/<uuid:task_id>/tags/remove/", views.task_remove_tag, name="task-remove-tag"),

    # Onboarding API
    path("onboarding/status/", views.onboarding_status, name="onboarding-status"),
    path("onboarding/complete/", views.onboarding_complete, name="onboarding-complete"),

    # Demo Data
    path("demo/seed/", views.seed_demo_data, name="demo-seed"),

    # Admin Endpoints
    path("admin/dashboard/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/broadcast/", views.admin_broadcast, name="admin-broadcast"),
    path("admin/reindex-all/", views.admin_reindex_all, name="admin-reindex-all"),

    # Analytics
    path("analytics/", get_analytics, name="analytics"),
    path("analytics/engagement/", get_user_engagement, name="analytics-engagement"),
    path("analytics/ai-usage/", get_ai_usage, name="analytics-ai-usage"),
    path("analytics/workspaces/<uuid:workspace_id>/", get_workspace_analytics, name="analytics-workspace"),
    path("analytics/admin/", get_admin_dashboard, name="analytics-admin"),
    path("analytics/retention/", get_retention_report, name="analytics-retention"),
    path("analytics/export/", request_analytics_export, name="analytics-export"),
    path("analytics/export/<uuid:export_id>/status/", get_export_status, name="analytics-export-status"),
    path("analytics/delete-data/", delete_analytics_data, name="analytics-delete"),
    
    # Notifications
    path("notifications/", views.get_notifications, name="notifications-list"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="notification-mark-read"),

    # Async Operations
    path("async/process-document/", async_process_document, name="async-process-document"),
    path("async/bulk-task-update/", async_bulk_task_update, name="async-bulk-task-update"),
    path("async/jobs/<uuid:job_id>/status/", async_job_status, name="async-job-status"),

    # Semantic Search
    path("search/semantic/", semantic_search, name="semantic-search"),
    path("search/conversational/", conversational_retrieval, name="conversational-retrieval"),
    path("search/generate-embeddings/", generate_embeddings, name="generate-embeddings"),

    # API Documentation (p6-4)
    path("docs/openapi.json", get_openapi_spec, name="openapi-spec"),
    path("docs/", api_documentation, name="api-docs"),
    path("docs/examples/", get_api_examples, name="api-examples"),

    # API Token Management (p6-1)
    path("tokens/", list_api_tokens, name="api-token-list"),
    path("tokens/create/", create_api_token, name="api-token-create"),
    path("tokens/<uuid:token_id>/revoke/", revoke_api_token, name="api-token-revoke"),

    # Zapier/Make Integration (p6-3)
    path("integrations/status/", integration_status, name="integration-status"),
    path("integrations/zapier/triggers/", zapier_triggers, name="zapier-triggers"),
    path("integrations/zapier/actions/", zapier_actions, name="zapier-actions"),
    path("integrations/zapier/samples/<str:trigger_key>/", zapier_sample_data, name="zapier-samples"),

    # Webhook System (p6-2)
    path("webhooks/", list_webhooks, name="webhook-list"),
    path("webhooks/create/", create_webhook, name="webhook-create"),
    path("webhooks/events/", get_available_events, name="webhook-events"),
    path("webhooks/<uuid:webhook_id>/", get_webhook, name="webhook-detail"),
    path("webhooks/<uuid:webhook_id>/update/", update_webhook, name="webhook-update"),
    path("webhooks/<uuid:webhook_id>/delete/", delete_webhook, name="webhook-delete"),
    path("webhooks/<uuid:webhook_id>/test/", test_webhook, name="webhook-test"),
    path("webhooks/<uuid:webhook_id>/deliveries/", list_deliveries, name="webhook-deliveries"),
    path("webhooks/<uuid:webhook_id>/regenerate-secret/", regenerate_secret, name="webhook-regenerate-secret"),

    # Permissions & Workspace Management
    path("workspaces/", list_workspaces, name="workspace-list"),
    path("workspaces/create/", create_workspace, name="workspace-create"),
    path("workspaces/<uuid:workspace_id>/", get_workspace, name="workspace-detail"),
    path("workspaces/<uuid:workspace_id>/update/", update_workspace, name="workspace-update"),
    path("workspaces/<uuid:workspace_id>/delete/", delete_workspace, name="workspace-delete"),
    path("workspaces/<uuid:workspace_id>/members/", list_members, name="workspace-members"),
    path("workspaces/<uuid:workspace_id>/members/invite/", invite_member, name="workspace-invite"),
    path("workspaces/<uuid:workspace_id>/members/<uuid:member_id>/role/", update_member_role, name="member-role-update"),
    path("workspaces/<uuid:workspace_id>/members/<uuid:member_id>/remove/", remove_member, name="member-remove"),
    path("workspaces/<uuid:workspace_id>/check-permission/", check_permission, name="check-permission"),
    path("permissions/resource-check/", check_resource_permission, name="resource-permission-check"),
    path("permissions/grant/", grant_permission, name="permission-grant"),
    path("permissions/revoke/", revoke_permission, name="permission-revoke"),

    # AI-Generated Tasks
    path("conversations/<uuid:conversation_id>/generate-tasks/", generate_tasks_from_chat, name="generate-tasks-chat"),
    path("documents/<uuid:document_id>/generate-tasks/", generate_tasks_from_document, name="generate-tasks-document"),
    path("ai-tasks/pending/", get_pending_ai_tasks, name="ai-tasks-pending"),
    path("ai-tasks/<uuid:task_id>/accept/", accept_ai_task, name="ai-task-accept"),
    path("ai-tasks/<uuid:task_id>/reject/", reject_ai_task, name="ai-task-reject"),

    # Notifications (Real-time WebSocket)
    path("notifications/", get_notifications, name="notifications-list"),
    path("notifications/unread-count/", get_unread_count, name="notifications-unread-count"),
    path("notifications/<uuid:notification_id>/read/", mark_notification_read, name="notification-mark-read"),
    path("notifications/mark-all-read/", mark_all_read, name="notifications-mark-all-read"),
    path("notifications/preferences/", get_notification_preferences, name="notification-preferences"),
    path("notifications/preferences/update/", update_notification_preferences, name="notification-preferences-update"),

    # Document Analysis & Auto-Extraction
    path("documents/<uuid:document_id>/analyze/", analyze_document, name="document-analyze"),
    path("documents/<uuid:document_id>/extract/", auto_extract_tasks, name="document-auto-extract"),
    path("documents/<uuid:document_id>/insights/", get_document_insights, name="document-insights"),

    # Document Versioning
    path("documents/<uuid:document_id>/versions/", list_document_versions, name="document-versions"),
    path("documents/<uuid:document_id>/versions/<int:version_number>/diff/", get_version_diff, name="document-version-diff"),
    path("documents/<uuid:document_id>/versions/compare/", compare_versions, name="document-versions-compare"),
    path("documents/<uuid:document_id>/versions/create/", create_version, name="document-version-create"),

    # Workspace Context & AI Memory
    path("workspaces/", list_workspaces, name="workspace-list"),
    path("workspaces/<str:workspace_id>/context/", get_workspace_context, name="workspace-context"),
    path("workspaces/<str:workspace_id>/context/update/", update_business_context, name="workspace-context-update"),
    path("workspaces/<str:workspace_id>/memories/", get_memories, name="workspace-memories"),
    path("workspaces/<str:workspace_id>/memories/add/", add_memory, name="workspace-memory-add"),
    path("workspaces/<str:workspace_id>/memories/<int:memory_index>/delete/", delete_memory, name="workspace-memory-delete"),
    path("workspaces/<str:workspace_id>/conversations/summarize/", add_conversation_summary, name="workspace-conversation-summarize"),
    path("workspaces/<str:workspace_id>/preferences/", update_preferences, name="workspace-preferences"),
    path("workspaces/<str:workspace_id>/archive/", archive_workspace, name="workspace-archive"),
]
