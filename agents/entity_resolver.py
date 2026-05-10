"""
Entity resolution layer.
Resolves demonstrative and possessive references to specific DB entities.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ResolvedEntity:
    type: str           # "document", "task", "contact"
    id: Optional[str]
    name: str
    confidence: float   # 0.0 to 1.0
    needs_clarification: bool


class EntityResolver:

    DOCUMENT_NOUNS = {"report", "document", "file", "pdf", "attachment", "doc"}
    TASK_NOUNS = {"task", "todo", "item", "reminder", "action"}

    def __init__(self, user_id: int, conversation_history: List[dict]):
        self.user_id = user_id
        self.history = conversation_history

    def resolve(self, text: str) -> List[ResolvedEntity]:
        entities = []
        text_lower = text.lower()

        # Pattern: "that/this/the <noun>"
        demo_pattern = r'\b(that|this|those|the)\s+(\w+)'
        for match in re.finditer(demo_pattern, text_lower):
            noun = match.group(2)
            if noun in self.DOCUMENT_NOUNS:
                entity = self._resolve_document_from_history()
                if entity:
                    entities.append(entity)
            elif noun in self.TASK_NOUNS:
                entity = self._resolve_task_from_history()
                if entity:
                    entities.append(entity)

        # Pattern: "my <noun>"
        poss_pattern = r'\bmy\s+(\w+)'
        for match in re.finditer(poss_pattern, text_lower):
            noun = match.group(1)
            if noun in self.DOCUMENT_NOUNS and not any(e.type == "document" for e in entities):
                entity = self._resolve_recent_document()
                if entity:
                    entities.append(entity)
            elif noun in self.TASK_NOUNS and not any(e.type == "task" for e in entities):
                entity = self._resolve_recent_task()
                if entity:
                    entities.append(entity)

        return entities

    def _resolve_document_from_history(self) -> Optional[ResolvedEntity]:
        """Find the most recently mentioned document UUID in conversation history."""
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        for msg in reversed(self.history[-8:]):
            content = msg.get("content", "")
            uuids = re.findall(uuid_pattern, content, re.IGNORECASE)
            if uuids:
                try:
                    from core.models import Document
                    doc = Document.objects.get(id=uuids[-1], user_id=self.user_id)
                    return ResolvedEntity(
                        type="document",
                        id=str(doc.id),
                        name=doc.title,
                        confidence=0.85,
                        needs_clarification=False
                    )
                except Exception:
                    pass
        return self._resolve_recent_document()

    def _resolve_recent_document(self) -> Optional[ResolvedEntity]:
        """Fall back to most recently updated document."""
        try:
            from core.models import Document
            doc = Document.objects.filter(
                user_id=self.user_id
            ).order_by('-updated_at').first()
            if doc:
                return ResolvedEntity(
                    type="document",
                    id=str(doc.id),
                    name=doc.title,
                    confidence=0.55,
                    needs_clarification=True
                )
        except Exception:
            pass
        return None

    def _resolve_task_from_history(self) -> Optional[ResolvedEntity]:
        """Find the most recently mentioned task UUID in conversation history."""
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        for msg in reversed(self.history[-8:]):
            content = msg.get("content", "")
            uuids = re.findall(uuid_pattern, content, re.IGNORECASE)
            if uuids:
                try:
                    from core.models import Task
                    task = Task.objects.get(id=uuids[-1], user_id=self.user_id)
                    return ResolvedEntity(
                        type="task",
                        id=str(task.id),
                        name=task.title,
                        confidence=0.85,
                        needs_clarification=False
                    )
                except Exception:
                    pass
        return self._resolve_recent_task()

    def _resolve_recent_task(self) -> Optional[ResolvedEntity]:
        try:
            from core.models import Task
            task = Task.objects.filter(
                user_id=self.user_id,
                status__in=["todo", "in_progress"]
            ).order_by('-updated_at').first()
            if task:
                return ResolvedEntity(
                    type="task",
                    id=str(task.id),
                    name=task.title,
                    confidence=0.55,
                    needs_clarification=True
                )
        except Exception:
            pass
        return None
