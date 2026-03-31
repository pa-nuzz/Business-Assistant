from django.urls import path
from api import views

urlpatterns = [
    # Health
    path("health/", views.health_check, name="health-check"),

    # Auth
    path("auth/register/", views.register, name="register"),

    # Chat
    path("chat/", views.chat, name="chat"),
    path("chat/stream/", views.chat_stream, name="chat-stream"),
    path("conversations/", views.conversation_list, name="conversation-list"),
    path("conversations/<uuid:conversation_id>/", views.conversation_detail, name="conversation-detail"),
    path("conversations/<uuid:conversation_id>/delete/", views.delete_conversation, name="delete-conversation"),

    # Documents
    path("documents/", views.document_list, name="document-list"),
    path("documents/upload/", views.upload_document, name="upload-document"),
    path("documents/<uuid:doc_id>/status/", views.document_status, name="document-status"),
    path("documents/<uuid:doc_id>/delete/", views.delete_document, name="delete-document"),

    # Business Profile
    path("profile/", views.business_profile, name="business-profile"),
]
