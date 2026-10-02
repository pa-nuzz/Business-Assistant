"""Document analysis and auto-extraction service."""
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from core.models import Document, Task, DocumentChunk
from core.services.semantic_service import SemanticSearchService
from services.model_layer import call_model, TaskType, Priority
from services.gemini import call_vision
import logging

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """Service for AI-powered document analysis and auto-extraction."""

    def __init__(self, user: User):
        self.user = user

    def analyze_document(self, document: Document) -> Dict[str, Any]:
        """
        Analyze a document and extract insights using LLM.
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
        
        # Combine all content (limit for token budget)
        all_content = ' '.join([c.content for c in chunks])
        content_preview = all_content[:8000]  # ~2k tokens
        
        # Generate AI-powered analysis
        try:
            analysis = self._generate_ai_analysis(document, content_preview, total_chunks)
        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            analysis = self._generate_fallback_analysis(document, chunks)
        
        return analysis

    def _generate_ai_analysis(self, document: Document, content: str, total_chunks: int) -> Dict[str, Any]:
        """Generate AI-powered document analysis."""
        
        analysis_prompt = f"""Analyze this business document titled '{document.title}' and provide a comprehensive analysis.

Document content (first 8000 chars):
{content}

Provide a JSON response with exactly these fields:
{{
  "summary": "2-3 sentence executive summary",
  "key_topics": ["topic1", "topic2", "topic3"],
  "document_type": "contract|invoice|report|proposal|cv|email|other",
  "business_entities": {{
    "companies": ["company1", "company2"],
    "people": ["person1", "person2"],
    "dates": ["date1", "date2"],
    "amounts": ["amount1", "amount2"],
    "locations": ["location1"]
  }},
  "suggested_tasks": [
    {{"title": "Task title", "description": "Task description", "priority": "high|medium|low", "category": "review|finance|schedule|compliance|general", "confidence": 0.0-1.0}}
  ],
  "key_insights": ["insight1", "insight2"],
  "risk_flags": ["risk1", "risk2"],
  "action_items": ["action1", "action2"]
}}

Only output valid JSON. No markdown, no extra text."""

        result = call_model(
            user_id=self.user.id,
            user_message=analysis_prompt,
            base_system_prompt="You are a business document analyzer. Extract structured insights from documents. Output only valid JSON.",
            task_type=TaskType.ANALYSIS,
            priority=Priority.HIGH,
            use_cache=False,
        )
        
        # Parse JSON response
        import json
        try:
            ai_result = json.loads(result.text.strip())
        except json.JSONDecodeError:
            # Try to extract JSON from markdown blocks
            text = result.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            ai_result = json.loads(text)
        
        # Get keywords from chunks
        chunks = DocumentChunk.objects.filter(document_id=document.id)
        key_topics = self._extract_keywords(chunks)
        
        # Add document metadata
        ai_result.update({
            'document_id': str(document.id),
            'document_title': document.title,
            'status': 'analyzed',
            'key_topics': key_topics,
            'total_chunks_analyzed': total_chunks,
            'content_length': len(content),
        })
        
        return ai_result
    
    def _generate_fallback_analysis(self, document: Document, chunks) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable."""
        content = ' '.join([c.content for c in chunks])
        content_preview = content[:4000]
        
        return {
            'document_id': str(document.id),
            'document_title': document.title,
            'status': 'analyzed_fallback',
            'summary': self._generate_placeholder_summary(content_preview),
            'key_topics': self._extract_keywords(chunks),
            'document_type': 'unknown',
            'business_entities': {},
            'suggested_tasks': self._suggest_tasks_placeholder(content),
            'key_insights': [],
            'risk_flags': [],
            'action_items': [],
            'total_chunks_analyzed': chunks.count(),
            'content_length': len(content),
            'note': 'AI analysis unavailable - using fallback analysis'
        }

    def _generate_placeholder_summary(self, content: str) -> str:
        """Generate a placeholder summary."""
        sentences = content.split('.')[:3]
        return '. '.join(sentences) + '.' if sentences else "No summary available."

    def _extract_keywords(self, chunks) -> List[str]:
        """Extract keywords from chunks."""
        all_keywords = set()
        for chunk in chunks:
            all_keywords.update(chunk.keywords)
        return list(all_keywords)[:10]

    def _suggest_tasks_placeholder(self, content: str) -> List[Dict[str, Any]]:
        """Generate placeholder task suggestions based on content."""
        suggested_tasks = []
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
        """
        created_tasks = []
        
        for suggestion in suggestions:
            task = Task.objects.create(
                user=self.user,
                created_by=self.user,
                business_profile=self.user.business_profile,
                title=suggestion['title'],
                description=suggestion['description'],
                priority=suggestion['priority'],
                status='todo',
                source_document=document,
                auto_extracted=True,
            )
            created_tasks.append(task)
        
        return created_tasks

    def extract_entities(self, document: Document) -> Dict[str, List[str]]:
        """
        Extract named entities from document.
        """
        chunks = DocumentChunk.objects.filter(document=document)
        all_content = ' '.join([c.content for c in chunks])
        
        # Use AI for entity extraction
        try:
            entity_prompt = f"""Extract named entities from this document. Return JSON only.

Content: {all_content[:4000]}

Return exactly:
{{
  "people": [],
  "organizations": [],
  "dates": [],
  "locations": [],
  "amounts": [],
  "emails": [],
  "urls": []
}}"""

            result = call_model(
                user_id=self.user.id,
                user_message=entity_prompt,
                base_system_prompt="You are a named entity recognition system. Extract entities from text. Output only valid JSON.",
                task_type=TaskType.ANALYSIS,
                priority=Priority.HIGH,
                use_cache=False,
            )
            
            import json
            try:
                entities = json.loads(result.text.strip())
            except json.JSONDecodeError:
                text = result.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                entities = json.loads(text)
        except Exception as e:
            logger.warning(f"AI entity extraction failed, using fallback: {e}")
            entities = self._extract_entities_fallback(all_content)
        
        return entities
    
    def _extract_entities_fallback(self, content: str) -> Dict[str, List[str]]:
        """Fallback entity extraction using regex patterns."""
        import re
        
        entities = {
            'people': [],
            'organizations': [],
            'dates': self._extract_dates_placeholder(content),
            'locations': [],
            'amounts': self._extract_amounts_placeholder(content),
            'emails': self._extract_emails(content),
            'urls': self._extract_urls(content)
        }
        
        return entities

    def _extract_dates_placeholder(self, content: str) -> List[str]:
        import re
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(dates))[:5]

    def _extract_emails(self, content: str) -> List[str]:
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, content)
        return list(set(emails))[:5]

    def _extract_amounts_placeholder(self, content: str) -> List[str]:
        import re
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|\$)',
        ]
        amounts = []
        for pattern in patterns:
            amounts.extend(re.findall(pattern, content))
        return list(set(amounts))[:5]

    def _extract_urls(self, content: str) -> List[str]:
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
