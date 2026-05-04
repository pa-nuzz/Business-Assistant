"""Document analysis and auto-extraction service."""
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from core.models import Document, Task, DocumentChunk
from core.services.semantic_service import SemanticSearchService
import logging

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """Service for AI-powered document analysis and auto-extraction."""

    def __init__(self, user: User):
        self.user = user

    def analyze_document(self, document: Document) -> Dict[str, Any]:
        """
        Analyze a document and extract insights.
        
        This is a placeholder implementation. In production:
        1. Call LLM to summarize document content
        2. Extract key entities, dates, action items
        3. Generate suggested tasks
        """
        logger.info(f"Analyzing document {document.id} for user {self.user.id}")
        
        # Get document chunks for analysis
        chunks = DocumentChunk.objects.filter(document=document)
        total_chunks = chunks.count()
        
        if total_chunks == 0:
            return {
                'document_id': str(document.id),
                'status': 'no_content',
                'message': 'Document has no extracted text to analyze'
            }
        
        # Combine all content (limit to first ~4000 chars for summary)
        all_content = ' '.join([c.content for c in chunks])
        content_preview = all_content[:4000]
        
        # Placeholder analysis results
        # In production, this would call the LLM
        analysis = {
            'document_id': str(document.id),
            'document_title': document.title,
            'status': 'analyzed',
            'summary': self._generate_placeholder_summary(content_preview),
            'key_topics': self._extract_keywords(chunks),
            'suggested_tasks': self._suggest_tasks_placeholder(content_preview),
            'total_chunks_analyzed': total_chunks,
            'content_length': len(all_content),
            'note': 'AI analysis is in placeholder mode. Enable LLM integration for full functionality.'
        }
        
        return analysis

    def _generate_placeholder_summary(self, content: str) -> str:
        """Generate a placeholder summary."""
        # In production: Call LLM to generate summary
        # For now, return first 200 chars as "summary"
        sentences = content.split('.')[:3]
        return '. '.join(sentences) + '.' if sentences else "No summary available."

    def _extract_keywords(self, chunks) -> List[str]:
        """Extract keywords from chunks."""
        # Aggregate all keywords from chunks
        all_keywords = set()
        for chunk in chunks:
            all_keywords.update(chunk.keywords)
        return list(all_keywords)[:10]  # Top 10 keywords

    def _suggest_tasks_placeholder(self, content: str) -> List[Dict[str, Any]]:
        """Generate placeholder task suggestions based on content."""
        suggested_tasks = []
        
        # Simple keyword-based task suggestions
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['deadline', 'due', 'by', 'before']):
            suggested_tasks.append({
                'title': 'Review document deadlines',
                'description': 'Check for any deadlines mentioned in this document',
                'priority': 'high',
                'category': 'review',
                'confidence': 0.8
            })
        
        if any(word in content_lower for word in ['contract', 'agreement', 'terms']):
            suggested_tasks.append({
                'title': 'Review contract terms',
                'description': 'This appears to be a contract. Review all terms carefully.',
                'priority': 'high',
                'category': 'review',
                'confidence': 0.85
            })
        
        if any(word in content_lower for word in ['invoice', 'payment', 'bill', 'amount']):
            suggested_tasks.append({
                'title': 'Process invoice payment',
                'description': 'This document appears to be an invoice. Process payment if approved.',
                'priority': 'medium',
                'category': 'finance',
                'confidence': 0.75
            })
        
        if any(word in content_lower for word in ['meeting', 'schedule', 'appointment']):
            suggested_tasks.append({
                'title': 'Schedule follow-up meeting',
                'description': 'Review meeting details and add to calendar',
                'priority': 'medium',
                'category': 'schedule',
                'confidence': 0.7
            })
        
        # Always suggest a generic review task
        if not suggested_tasks:
            suggested_tasks.append({
                'title': 'Review uploaded document',
                'description': 'Review and process this document',
                'priority': 'low',
                'category': 'review',
                'confidence': 0.5
            })
        
        return suggested_tasks

    def create_tasks_from_suggestions(self, document: Document, suggestions: List[Dict]) -> List[Task]:
        """
        Create actual Task objects from AI suggestions.
        
        In production: Would create tasks in database
        For now: Returns what tasks would be created
        """
        created_tasks = []
        
        for suggestion in suggestions:
            # In production, create actual Task objects
            # task = Task.objects.create(
            #     user=self.user,
            #     title=suggestion['title'],
            #     description=suggestion['description'],
            #     priority=suggestion['priority'],
            #     source_document=document,
            #     auto_extracted=True
            # )
            # created_tasks.append(task)
            
            # For now, just return the suggestion
            created_tasks.append(suggestion)
        
        return created_tasks

    def extract_entities(self, document: Document) -> Dict[str, List[str]]:
        """
        Extract named entities from document.
        
        Entities: people, organizations, dates, locations, amounts
        """
        chunks = DocumentChunk.objects.filter(document=document)
        all_content = ' '.join([c.content for c in chunks])
        
        # Placeholder: simple pattern matching
        # In production, use NER (Named Entity Recognition) model
        entities = {
            'dates': self._extract_dates_placeholder(all_content),
            'emails': self._extract_emails(all_content),
            'amounts': self._extract_amounts_placeholder(all_content),
            'urls': self._extract_urls(all_content)
        }
        
        return entities

    def _extract_dates_placeholder(self, content: str) -> List[str]:
        """Extract dates using simple patterns (placeholder)."""
        import re
        # Simple date patterns MM/DD/YYYY or MM-DD-YYYY
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(dates))[:5]  # Deduplicate and limit

    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses."""
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, content)
        return list(set(emails))[:5]

    def _extract_amounts_placeholder(self, content: str) -> List[str]:
        """Extract monetary amounts (placeholder)."""
        import re
        # Match currency patterns like $1,234.56 or 1,234 USD
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|\$)',
        ]
        amounts = []
        for pattern in patterns:
            amounts.extend(re.findall(pattern, content))
        return list(set(amounts))[:5]

    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs."""
        import re
        pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
        urls = re.findall(pattern, content)
        return list(set(urls))[:5]


class DocumentProcessingPipeline:
    """
    End-to-end document processing pipeline.
    
    Handles: upload -> text extraction -> AI analysis -> task suggestions
    """

    def __init__(self, user: User):
        self.user = user
        self.analysis_service = DocumentAnalysisService(user)

    def process_document(self, document: Document, auto_create_tasks: bool = False) -> Dict[str, Any]:
        """
        Run full document processing pipeline.
        
        Args:
            document: The Document to process
            auto_create_tasks: If True, automatically create tasks (default: False for review first)
        
        Returns:
            Full processing results including analysis and task suggestions
        """
        logger.info(f"Running processing pipeline for document {document.id}")
        
        # Step 1: Analyze document
        analysis = self.analysis_service.analyze_document(document)
        
        # Step 2: Extract entities
        entities = self.analysis_service.extract_entities(document)
        analysis['extracted_entities'] = entities
        
        # Step 3: Create tasks if requested
        created_tasks = []
        if auto_create_tasks and analysis.get('suggested_tasks'):
            created_tasks = self.analysis_service.create_tasks_from_suggestions(
                document, 
                analysis['suggested_tasks']
            )
        
        return {
            'document_id': str(document.id),
            'processing_status': 'completed',
            'analysis': analysis,
            'tasks_created': len(created_tasks),
            'tasks': created_tasks if auto_create_tasks else [],
            'tasks_pending_review': analysis.get('suggested_tasks', []) if not auto_create_tasks else [],
            'auto_extraction_enabled': auto_create_tasks
        }
