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
        raise self.retry(exc=exc, countdown=10)
