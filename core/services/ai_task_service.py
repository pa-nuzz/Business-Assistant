"""AI-Generated Tasks Service - Create tasks from chat messages and document analysis."""
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from core.models import Task, Document, Conversation, DocumentChunk
import logging

logger = logging.getLogger(__name__)


class AITaskGenerationService:
    """Service for generating tasks from various AI-analyzed content."""

    def __init__(self, user: User):
        self.user = user

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
        """
        Extract task suggestions from text using LLM.
        Decomposes complex tasks into manageable sub-tasks.
        """
        from services.model_layer import call_model, TaskType, Priority
        
        # Limit text for analysis
        analysis_text = text[:8000]
        
        prompt = f"""Analyze the following {context} content and identify actionable tasks.
1. Provide a clear, professional title.
2. Provide a detailed description.
3. Assign a priority (low, medium, high, urgent).
4. Assign a work_mode:
   - "deep_work": Requires high focus (writing, coding, strategy).
   - "creative": Ideation, design, brainstorming.
   - "admin": Emails, scheduling, simple updates.
   - "quick": Tasks taking < 10 mins.
5. Extract a due date if mentioned (use YYYY-MM-DD format).
6. If the task is complex, break it down into 3-5 logical sub-tasks.

Content to analyze:
"{analysis_text}"

Return the result as a JSON list of tasks, like this:
[
  {{
    "title": "Task title",
    "description": "Task description",
    "priority": "medium",
    "work_mode": "deep_work",
    "due_date": "2026-05-20",
    "subtasks": ["Subtask 1", "Subtask 2"]
  }}
]
If no tasks are found, return an empty list []. Respond ONLY with the JSON."""

        try:
            result = call_model(
                user_id=self.user.id,
                user_message=prompt,
                base_system_prompt="You are an expert project manager and task extractor.",
                task_type=TaskType.ANALYSIS,
                priority=Priority.HIGH,
                use_cache=True
            )
            
            import json
            # Clean response if it contains markdown code blocks
            clean_text = result.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()
                
            suggestions = json.loads(clean_text)
            
            # Enrich suggestions with metadata
            for s in suggestions:
                s['source_context'] = context
                s['confidence'] = 0.9
                
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"LLM task extraction failed: {e}")
            return []

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
    ) -> List[Dict[str, Any]]:
        """Create actual Task objects and their sub-tasks from suggestions."""
        from core.models import TaskSubtask, BusinessProfile
        created_data = []
        
        try:
            profile = BusinessProfile.objects.get(user=self.user)
        except BusinessProfile.DoesNotExist:
            profile = BusinessProfile.objects.create(user=self.user, company_name="Personal")
        
        for suggestion in suggestions:
            task = Task.objects.create(
                user=self.user,
                created_by=self.user,
                business_profile=profile,
                title=suggestion['title'],
                description=suggestion['description'],
                priority=suggestion.get('priority', 'medium'),
                work_mode=suggestion.get('work_mode', 'quick'),
                due_date=suggestion.get('due_date'),
                status='todo',
                auto_extracted=True,
                source_document=source_document,
                ai_metadata={
                    'confidence': suggestion.get('confidence'),
                    'source_context': suggestion.get('source_context'),
                    'has_subtasks': bool(suggestion.get('subtasks'))
                }
            )
            
            # Create sub-tasks if present
            subtasks = suggestion.get('subtasks', [])
            for st_title in subtasks:
                TaskSubtask.objects.create(
                    parent_task=task,
                    title=st_title,
                    status='todo'
                )
            
            created_data.append({
                'id': str(task.id),
                'title': task.title,
                'work_mode': task.work_mode,
                'subtask_count': len(subtasks)
            })
        
        return created_data

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
