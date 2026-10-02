"""
Celery tasks for background processing.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_task(self, doc_id: str):
    """
    Process a document in the background.
    Called via .delay() from the upload view.
    """
    from services.document import process_document

    try:
        success = process_document(doc_id)
        if success:
            logger.info(f"Document {doc_id} processed successfully")
        else:
            logger.warning(f"Document {doc_id} processing failed")
        return {"doc_id": doc_id, "success": success}
    except Exception as exc:
        logger.exception(f"Document processing task failed for {doc_id}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=1, soft_time_limit=30, time_limit=60)
def defer_memory_extraction(self, user_id: int, user_message: str, ai_response: str):
    """
    Extract and store important facts from a conversation turn.
    Runs as a background task to avoid blocking responses with an extra LLM call.
    """
    from services.model_layer import extract_and_store_memory

    try:
        stored = extract_and_store_memory(user_id, user_message, ai_response)
        if stored:
            logger.info(f"Memory extracted for user {user_id}")
        return {"user_id": user_id, "stored": stored}
    except Exception as exc:
        logger.warning(f"Memory extraction task failed for user {user_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 *(2**self.request.retries))


@shared_task(bind=True, max_retries=1, soft_time_limit=300, time_limit=360)
def summarize_conversations_task(self):
    """
    Summarize recent conversations across all workspaces.
    Runs daily via Celery Beat to build long-term conversation memory.

    Scope is derived from the resource being processed — never from any
    browser/session "active workspace":
        Conversation → Conversation.workspace → WorkspaceContext

    Summaries are never mixed between workspaces: each conversation's
    summary is written to its own workspace's shared context.
    """
    from django.contrib.auth import get_user_model
    from core.models import Conversation, Workspace, WorkspaceContext
    from services.model_layer import call_model, TaskType, Priority
    from django.utils import timezone
    from datetime import timedelta

    User = get_user_model()
    summarized_count = 0
    error_count = 0

    try:
        week_ago = timezone.now() - timedelta(days=7)

        # Recent, non-deleted conversations that belong to a workspace.
        # (All conversations were backfilled to a workspace in migration 0027;
        # workspace-less rows, if any, are skipped until assigned.)
        recent_conversations = Conversation.objects.filter(
            created_at__gte=week_ago,
            deleted_at__isnull=True,
            workspace__isnull=False,
        ).exclude(
            workspace__context__isnull=False,
        ).select_related("user", "workspace")[:50]

        # Also include conversations whose workspace HAS a context but which
        # are not yet summarized in it.
        candidate_ids = set(recent_conversations.values_list("id", flat=True))

        unsummarized = []
        for convo in Conversation.objects.filter(
            id__in=candidate_ids,
            created_at__gte=week_ago,
            deleted_at__isnull=True,
        ).select_related("user", "workspace", "workspace__context"):
            summaries = getattr(convo.workspace, "context", None)
            summarized_ids = set()
            if summaries:
                summarized_ids = {
                    s.get("conversation_id")
                    for s in summaries.conversation_summaries
                    if s.get("conversation_id")
                }
            if str(convo.id) not in summarized_ids:
                unsummarized.append(convo)

        for convo in unsummarized:
            try:
                # Get or create the conversation's workspace shared context
                workspace_ctx, _ = WorkspaceContext.objects.get_or_create(
                    workspace=convo.workspace,
                    defaults={
                        "business_context": {},
                        "ai_memory": [],
                        "conversation_summaries": [],
                        "preferences": {},
                    }
                )

                messages = convo.messages.order_by("created_at")
                if messages.count() < 3:
                    continue  # Skip very short conversations

                # Build conversation text for summarization
                message_texts = []
                for msg in messages:
                    role = "User" if msg.role == "user" else "Assistant"
                    message_texts.append(f"{role}: {msg.content}")
                
                conversation_text = "\n".join(message_texts)
                
                if len(conversation_text) < 100:
                    continue

                # Generate summary using LLM
                summary_prompt = f"""Summarize this business conversation in 2-3 sentences. Focus on:
- Key topics discussed
- Decisions made or action items
- Important facts or preferences revealed
- Any follow-up items needed

Conversation:
{conversation_text[:4000]}

Summary:"""

                result = call_model(
                    user_id=convo.user_id,
                    user_message=summary_prompt,
                    base_system_prompt="You are a business conversation summarizer. Be concise and factual.",
                    task_type=TaskType.ANALYSIS,
                    priority=Priority.NORMAL,
                    use_cache=False,
                )

                if result.text and result.text.strip():
                    summary_entry = {
                        "conversation_id": str(convo.id),
                        "summary": result.text.strip(),
                        "topics": [],  # Could extract topics in future
                        "created_at": timezone.now().isoformat(),
                    }
                    
                    # Keep only last 20 summaries in this workspace's context
                    workspace_ctx.conversation_summaries = (
                        workspace_ctx.conversation_summaries[-19:] + [summary_entry]
                    )
                    workspace_ctx.save(update_fields=["conversation_summaries"])
                    summarized_count += 1

            except Exception as e:
                logger.warning(f"Failed to summarize conversation {convo.id} for workspace {convo.workspace_id}: {e}")
                error_count += 1

        logger.info(f"Conversation summarization complete: {summarized_count} summarized, {error_count} errors")
        return {"summarized": summarized_count, "errors": error_count}

    except Exception as exc:
        logger.exception("Conversation summarization task failed")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=0)
def cleanup_expired_sessions_task(self):
    """
    Clean up expired sessions and old audit logs.
    Runs daily via Celery Beat.
    """
    from django.contrib.auth import get_user_model
    from core.models import AuditLog, EmailVerification, PasswordResetCode
    from django.utils import timezone
    from datetime import timedelta

    User = get_user_model()
    cleaned_count = 0

    try:
        # Clean up expired email verifications (older than 15 minutes)
        expired_verifications = EmailVerification.objects.filter(
            created_at__lt=timezone.now() - timedelta(minutes=15),
            is_verified=False
        )
        count = expired_verifications.count()
        expired_verifications.delete()
        cleaned_count += count

        # Clean up expired password reset codes (older than 15 minutes)
        expired_resets = PasswordResetCode.objects.filter(
            created_at__lt=timezone.now() - timedelta(minutes=15),
            is_used=False
        )
        count = expired_resets.count()
        expired_resets.delete()
        cleaned_count += count

        # Clean up old audit logs (older than 90 days)
        old_audits = AuditLog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=90)
        )
        count = old_audits.count()
        old_audits.delete()
        cleaned_count += count

        logger.info(f"Session cleanup complete: {cleaned_count} records cleaned")
        return {"cleaned": cleaned_count}

    except Exception as exc:
        logger.exception("Session cleanup task failed")
        return {"error": str(exc)}


@shared_task(bind=True, max_retries=1, soft_time_limit=300, time_limit=360)
def generate_memory_embeddings_task(self, memory_ids: list = None):
    """
    Generate embeddings for UserMemory facts.
    Runs as a background task to avoid blocking responses.
    """
    from core.services.semantic_service import SemanticMemoryService
    
    try:
        result = SemanticMemoryService.generate_embeddings(memory_ids=memory_ids)
        return result
    except Exception as exc:
        logger.exception("Memory embedding generation task failed")
        raise self.retry(exc=exc, countdown=60)
    
