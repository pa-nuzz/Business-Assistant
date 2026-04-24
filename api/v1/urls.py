# API v1 URL Configuration
from django.urls import path
from api import views
from api.auth_views import (
    register, login, logout, verify_email, resend_verification,
    forgot_password, verify_reset_code, reset_password, token_refresh
)
from api.views import *  # Import all modular views
from api.task_views import (
    list_tasks, create_task, get_task, update_task, delete_task,
    complete_task, reopen_task, list_comments, create_comment, delete_comment,
    list_activities, task_dashboard, task_stats
)
from api.views.async_views import (
    async_process_document, async_bulk_task_update, async_job_status
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
    path("documents/<uuid:doc_id>/delete/", views.delete_document, name="delete-document"),
    path("documents/<uuid:doc_id>/summary/", views.document_summary, name="document-summary"),
    path("documents/<uuid:doc_id>/reindex/", views.reindex_document, name="document-reindex"),
    path("documents/<uuid:doc_id>/download/", views.document_download, name="document-download"),

    # Business Profile
    path("profile/", views.business_profile, name="business-profile"),
    path("analytics/", views.business_analytics, name="analytics"),

    # User Management
    path("user/update-username/", views.update_username, name="update-username"),
    path("user/update-password/", views.update_password, name="update-password"),
    path("user/info/", views.get_user_info, name="user-info"),

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

    # Notifications
    path("notifications/", views.get_notifications, name="notifications-list"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="notification-mark-read"),

    # Async Operations
    path("async/process-document/", async_process_document, name="async-process-document"),
    path("async/bulk-task-update/", async_bulk_task_update, name="async-bulk-task-update"),
    path("async/jobs/<uuid:job_id>/status/", async_job_status, name="async-job-status"),
]
