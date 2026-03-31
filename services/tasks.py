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
