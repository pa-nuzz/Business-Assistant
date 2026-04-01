"""
Document Processing Service.

Pipeline for uploaded files:
  upload → extract text → chunk → generate summary → store

Key design: we process ONCE, store everything. The agent never
re-reads the raw file — it reads chunks and summaries.
"""
import logging
import re
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text(file_path: str, file_type: str) -> tuple[str, int]:
    """
    Extract raw text from a document.
    Returns (text, page_count).
    """
    if file_type == "pdf":
        return _extract_pdf(file_path)
    elif file_type == "docx":
        return _extract_docx(file_path), 1
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return text, 1
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: str) -> tuple[str, int]:
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages), len(reader.pages)


def _extract_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = None, max_chunks: int = None) -> list[dict]:
    """
    Split text into overlapping chunks for retrieval.
    Returns list of {"content": str, "keywords": list[str], "chunk_index": int}

    Uses simple character-based chunking with sentence boundary awareness.
    No embeddings, no vector DB — just keyword-indexed chunks.
    """
    cfg = settings.DOCUMENT_CONFIG
    chunk_size = chunk_size or cfg["chunk_size_chars"]
    max_chunks = max_chunks or cfg["max_chunks_per_doc"]
    overlap = 150  # character overlap between chunks

    # Clean text
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    chunks = []
    start = 0
    idx = 0

    while start < len(text) and idx < max_chunks:
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence end within last 200 chars of chunk
            search_region = text[end - 200: end + 200]
            for sep in [". ", ".\n", "? ", "! ", "\n\n"]:
                pos = search_region.rfind(sep)
                if pos != -1:
                    end = end - 200 + pos + len(sep)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text:
            keywords = _extract_keywords(chunk_text)
            chunks.append({
                "content": chunk_text,
                "keywords": keywords,
                "chunk_index": idx,
            })
            idx += 1

        start = end - overlap  # overlap for context continuity

    return chunks


def _extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """
    Simple keyword extraction by frequency.
    No NLP library needed — just works well enough for retrieval.
    """
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "is", "was", "are", "were", "be", "been", "have", "has",
        "had", "do", "does", "did", "will", "would", "can", "could", "should",
        "this", "that", "these", "those", "it", "its", "by", "from", "as",
        "not", "no", "so", "if", "then", "than", "when", "which", "who",
    }
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    freq = {}
    for word in words:
        if word not in STOPWORDS:
            freq[word] = freq.get(word, 0) + 1
    sorted_words = sorted(freq, key=freq.get, reverse=True)
    return sorted_words[:top_n]


# ─── Summary Generation ───────────────────────────────────────────────────────

def extract_business_context(text: str, doc_title: str, user_id: int) -> dict:
    """
    Extract business-relevant context from document and save to user memory.
    Identifies: company info, metrics, goals, projects, contacts, etc.
    """
    from agents.router import call_with_fallback
    from services.model_layer import add_user_memory
    
    excerpt = text[:6000]  # First 6000 chars for analysis
    if len(text) > 6000:
        excerpt += f"\n\n[Document truncated... {len(text) - 6000} more characters]"
    
    messages = [{
        "role": "user",
        "content": (
            f"Analyze this business document titled '{doc_title}' and extract key business context.\n\n"
            f"Identify and list any of these if present:\n"
            f"- Company/business name and description\n"
            f"- Key metrics (revenue, growth, customer count, etc.)\n"
            f"- Business goals or objectives\n"
            f"- Projects or initiatives\n"
            f"- Important contacts or stakeholders\n"
            f"- Products/services mentioned\n"
            f"- Market/industry insights\n"
            f"- Any other business-relevant information\n\n"
            f"Format each finding as: CATEGORY: specific detail\n"
            f"If nothing business-relevant is found, say 'NO_BUSINESS_CONTEXT'\n\n"
            f"Document:\n{excerpt}"
        ),
    }]
    
    try:
        response = call_with_fallback(
            messages=messages,
            system_prompt="You are a business analyst. Extract factual business information only. Be concise.",
            tool_definitions=[],
        )
        analysis = response.get("text", "")
        
        if "NO_BUSINESS_CONTEXT" in analysis or not analysis.strip():
            return {"found": False, "context": None}
        
        # Save to user memory for future context
        add_user_memory(
            user_id=user_id,
            key=f"doc_context_{doc_title.lower().replace(' ', '_')[:30]}",
            value=f"From document '{doc_title}': {analysis[:1000]}",
            category="document_insight",
        )
        
        # Also extract specific metrics if mentioned
        metrics = _extract_metrics_from_text(text)
        if metrics:
            for metric_name, metric_value in metrics.items():
                add_user_memory(
                    user_id=user_id,
                    key=f"metric_{metric_name}",
                    value=f"{metric_value} (from {doc_title})",
                    category="metric",
                )
        
        return {"found": True, "context": analysis, "metrics": metrics}
    except Exception as e:
        logger.warning(f"Business context extraction failed: {e}")
        return {"found": False, "error": str(e)}


def _extract_metrics_from_text(text: str) -> dict:
    """Extract numeric metrics like revenue, growth rate, etc."""
    import re
    metrics = {}
    
    # Revenue patterns
    revenue_patterns = [
        r'\$([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?\s*(?:USD|dollars?)?',
        r'revenue\s*(?:of|:|was|is)\s*\$?([\d,]+(?:\.\d+)?)',
        r'(?:annual|monthly|quarterly)\s+revenue[\s:]*\$?([\d,]+(?:\.\d+)?)',
    ]
    
    # Growth patterns
    growth_patterns = [
        r'(\d+(?:\.\d+)?)%\s*(?:growth|increase| YoY|year.over.year)',
        r'growth\s*(?:rate|of|:)\s*(\d+(?:\.\d+)?)',
    ]
    
    # Customer patterns
    customer_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:customers?|clients?|users?)',
        r'customer\s*(?:base|count|total)[\s:]*(\d+(?:,\d+)*)',
    ]
    
    for pattern in revenue_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            metrics['revenue'] = matches[0] if isinstance(matches[0], str) else matches[0][0]
            break
    
    for pattern in growth_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            metrics['growth_rate'] = f"{matches[0]}%"
            break
    
    for pattern in customer_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            metrics['customer_count'] = matches[0]
            break
    
    return metrics


# ─── Summary Generation ───────────────────────────────────────────────────────

def generate_summary(text: str, doc_title: str) -> str:
    """
    Generate a document summary using the primary AI model.
    Called once during processing — never again.
    Truncates to first 8000 chars to stay within token limits.
    """
    from agents.router import call_with_fallback

    # Use first 8000 chars (covers most docs without hitting token limits)
    excerpt = text[:8000]
    if len(text) > 8000:
        excerpt += f"\n\n[Document continues... {len(text) - 8000} more characters]"

    messages = [{
        "role": "user",
        "content": (
            f"Summarize this business document titled '{doc_title}'.\n\n"
            f"Focus on: main purpose, key findings/data, actionable insights, important numbers.\n"
            f"Keep it under 300 words. Be specific.\n\n"
            f"Document:\n{excerpt}"
        ),
    }]

    try:
        response = call_with_fallback(
            messages=messages,
            system_prompt="You are a precise business document summarizer. Extract key facts and insights.",
            tool_definitions=[],  # no tools needed for summarization
        )
        return response.get("text") or "Summary generation failed."
    except Exception as e:
        logger.exception("Failed to generate document summary")
        return f"Auto-summary unavailable. Document contains {len(text)} characters."


# ─── Full Processing Pipeline ─────────────────────────────────────────────────

def process_document(doc_id: str) -> bool:
    """
    Full pipeline: extract → chunk → summarize → save to DB.
    Call this from a background task (Celery) or inline for small files.
    Returns True on success.
    """
    from core.models import Document, DocumentChunk

    try:
        doc = Document.objects.get(id=doc_id)
        doc.status = "processing"
        doc.save(update_fields=["status"])

        # 1. Extract text
        file_path = doc.file.path
        text, page_count = extract_text(file_path, doc.file_type)

        if not text.strip():
            raise ValueError("No text could be extracted from document")

        # 2. Chunk
        cfg = settings.DOCUMENT_CONFIG
        chunks_data = chunk_text(
            text,
            chunk_size=cfg["chunk_size_chars"],
            max_chunks=cfg["max_chunks_per_doc"],
        )

        # 3. Generate summary
        summary = generate_summary(text, doc.title)

        # 3.5. Extract business context (async - don't block on failure)
        try:
            context_result = extract_business_context(text, doc.title, doc.user_id)
            if context_result.get("found"):
                logger.info(f"Business context extracted from {doc.title}")
        except Exception as e:
            logger.warning(f"Business context extraction skipped: {e}")

        # 4. Save everything
        # Delete old chunks if reprocessing
        DocumentChunk.objects.filter(document=doc).delete()

        chunk_objects = [
            DocumentChunk(
                document=doc,
                chunk_index=c["chunk_index"],
                content=c["content"],
                keywords=c["keywords"],
            )
            for c in chunks_data
        ]
        DocumentChunk.objects.bulk_create(chunk_objects)

        doc.summary = summary
        doc.page_count = page_count
        doc.status = "ready"
        doc.save(update_fields=["summary", "page_count", "status"])

        logger.info(
            f"Document processed: {doc.title} | "
            f"{page_count} pages | {len(chunks_data)} chunks"
        )
        return True

    except Exception as e:
        logger.exception(f"Document processing failed for {doc_id}")
        try:
            Document.objects.filter(id=doc_id).update(status="failed")
        except Exception:
            pass
        return False
