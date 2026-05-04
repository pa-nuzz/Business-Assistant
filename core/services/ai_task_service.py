"""AI-Generated Tasks Service - Create tasks from chat messages and document analysis."""
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from core.models import Task, Document, Conversation, DocumentChunk
from agents.orchestrator import Orchestrator
import logging

logger = logging.getLogger(__name__)


class AITaskGenerationService:
    """Service for generating tasks from various AI-analyzed content."""

    def __init__(self, user: User):
        self.user = user
        self.orchestrator = Orchestrator(user)

    def generate_tasks_from_chat(
        self, 
        conversation: Conversation,
        message_content: str,
        auto_create: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze chat message and suggest tasks.
        
        This is a placeholder implementation. In production:
        1. Use LLM to extract action items from the message
        2. Detect deadlines, priorities, assignees
        3. Return task suggestions
        """
        logger.info(f"Generating tasks from chat for user {self.user.id}")
        
        # Placeholder: Simple keyword-based task detection
        suggestions = self._extract_tasks_from_text(message_content)
        
        created_tasks = []
        if auto_create and suggestions:
            created_tasks = self._create_tasks_from_suggestions(suggestions)
        
        return {
            'source': 'chat',
            'source_id': str(conversation.id),
            'suggestions': suggestions,
            'tasks_created': len(created_tasks),
            'tasks': created_tasks if auto_create else [],
            'note': 'AI task generation is in placeholder mode. Enable LLM integration for full functionality.'
        }

    def generate_tasks_from_document(
        self,
        document: Document,
        auto_create: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze document and suggest tasks.
        Uses DocumentChunk content for analysis.
        """
        logger.info(f"Generating tasks from document {document.id}")
        
        # Get all document chunks
        chunks = DocumentChunk.objects.filter(document=document)
        full_text = ' '.join([chunk.content for chunk in chunks])
        
        # Placeholder: Keyword-based extraction
        suggestions = self._extract_tasks_from_text(full_text, context='document')
        
        created_tasks = []
        if auto_create and suggestions:
            created_tasks = self._create_tasks_from_suggestions(suggestions, source_document=document)
        
        return {
            'source': 'document',
            'source_id': str(document.id),
            'document_title': document.title,
            'suggestions': suggestions,
            'tasks_created': len(created_tasks),
            'tasks': created_tasks if auto_create else [],
            'note': 'AI task generation is in placeholder mode. Enable LLM integration for full functionality.'
        }

    def _extract_tasks_from_text(
        self, 
        text: str, 
        context: str = 'chat'
    ) -> List[Dict[str, Any]]:
        """Extract task suggestions from text using keyword patterns."""
        suggestions = []
        text_lower = text.lower()
        
        # Detect action keywords
        action_keywords = [
            ('schedule', 'Schedule a meeting/call'),
            ('remind', 'Set a reminder'),
            ('follow up', 'Follow up on this'),
            ('review', 'Review required'),
            ('approve', 'Approval needed'),
            ('send', 'Send email/document'),
            ('call', 'Make a phone call'),
            ('deadline', 'Deadline approaching'),
            ('todo', 'Action item'),
            ('task', 'New task identified'),
        ]
        
        for keyword, action_type in action_keywords:
            if keyword in text_lower:
                # Extract surrounding context (sentence containing keyword)
                idx = text_lower.find(keyword)
                start = max(0, text.rfind('.', 0, idx) + 1)
                end = text.find('.', idx)
                if end == -1:
                    end = len(text)
                
                context_text = text[start:end].strip()
                
                # Determine priority based on keywords
                priority = 'medium'
                if any(word in text_lower for word in ['urgent', 'asap', 'emergency', 'critical']):
                    priority = 'urgent'
                elif any(word in text_lower for word in ['important', 'high priority']):
                    priority = 'high'
                
                # Try to extract due date
                due_date = self._extract_due_date(text_lower)
                
                suggestion = {
                    'title': f"{action_type}: {context_text[:60]}..." if len(context_text) > 60 else action_type,
                    'description': context_text,
                    'priority': priority,
                    'due_date': due_date,
                    'source_context': context,
                    'confidence': 0.7,
                    'extracted_keywords': [keyword]
                }
                suggestions.append(suggestion)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_suggestions = []
        for s in suggestions:
            if s['title'] not in seen_titles:
                seen_titles.add(s['title'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:5]  # Limit to top 5 suggestions

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text using simple patterns."""
        import re
        from datetime import datetime, timedelta
        
        # Pattern: "by tomorrow", "by next week", "by Friday"
        date_patterns = [
            (r'by\s+tomorrow', lambda: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
            (r'by\s+next\s+week', lambda: (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')),
            (r'by\s+friday', lambda: self._next_friday()),
            (r'by\s+monday', lambda: self._next_monday()),
            (r'due\s+\d{1,2}/\d{1,2}/?\d{0,4}', lambda m: self._parse_date(m)),
        ]
        
        for pattern, date_func in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(date_func):
                        if match:
                            return date_func()
                        return date_func()
                except Exception:
                    continue
        
        return None

    def _next_friday(self) -> str:
        """Get next Friday's date."""
        from datetime import datetime, timedelta
        today = datetime.now()
        days_ahead = 4 - today.weekday()  # Friday is 4
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    def _next_monday(self) -> str:
        """Get next Monday's date."""
        from datetime import datetime, timedelta
        today = datetime.now()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    def _parse_date(self, match) -> str:
        """Parse date from regex match."""
        # Simple placeholder - in production use dateparser
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')

    def _create_tasks_from_suggestions(
        self, 
        suggestions: List[Dict], 
        source_document: Optional[Document] = None
    ) -> List[Task]:
        """Create actual Task objects from suggestions."""
        created = []
        
        for suggestion in suggestions:
            task = Task.objects.create(
                user=self.user,
                title=suggestion['title'],
                description=suggestion['description'],
                priority=suggestion.get('priority', 'medium'),
                due_date=suggestion.get('due_date'),
                status='todo',
                auto_extracted=True,
                source_document=source_document,
                ai_metadata={
                    'confidence': suggestion.get('confidence'),
                    'extracted_keywords': suggestion.get('extracted_keywords'),
                    'source_context': suggestion.get('source_context')
                }
            )
            created.append(task)
        
        return created

    def get_pending_ai_tasks(self) -> List[Dict[str, Any]]:
        """Get all AI-generated tasks that are pending review."""
        tasks = Task.objects.filter(
            user=self.user,
            auto_extracted=True,
            status='todo'
        ).order_by('-created_at')[:20]
        
        return [
            {
                'id': str(t.id),
                'title': t.title,
                'description': t.description,
                'priority': t.priority,
                'due_date': t.due_date,
                'ai_metadata': t.ai_metadata,
                'created_at': t.created_at.isoformat()
            }
            for t in tasks
        ]

    def accept_ai_task(self, task_id: str) -> bool:
        """Mark an AI task as accepted (keep it active)."""
        try:
            task = Task.objects.get(id=task_id, user=self.user, auto_extracted=True)
            # Task stays active, just mark as reviewed
            if task.ai_metadata:
                task.ai_metadata['reviewed'] = True
                task.ai_metadata['reviewed_at'] = datetime.now().isoformat()
                task.save(update_fields=['ai_metadata'])
            return True
        except Task.DoesNotExist:
            return False

    def reject_ai_task(self, task_id: str) -> bool:
        """Reject and delete an AI-generated task."""
        try:
            task = Task.objects.get(id=task_id, user=self.user, auto_extracted=True)
            task.delete()
            return True
        except Task.DoesNotExist:
            return False
