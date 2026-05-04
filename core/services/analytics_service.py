"""
Analytics service for generating user insights and dashboard data.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
from django.db.models import Count, Q, Avg
from django.contrib.auth.models import User
from core.models import (
    Conversation, Message, Document, Task, 
    BusinessProfile, TaskActivity
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and insights."""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard analytics."""
        profile = self._get_business_profile()
        
        return {
            "profile": profile,
            "summary": self._get_usage_summary(),
            "insights": self._generate_insights(),
            "activity_trends": self._get_activity_trends(),
            "followups": self._get_followups(),
            "recent_activity": self._get_recent_activity(),
        }
    
    def _get_business_profile(self) -> Dict[str, Any]:
        """Get user's business profile data."""
        try:
            profile = BusinessProfile.objects.get(user=self.user)
            return {
                "company_name": profile.company_name,
                "industry": profile.industry,
                "description": profile.description,
                "website": profile.website,
                "goals": profile.goals or [],
                "key_metrics": profile.key_metrics or {},
                "has_avatar": bool(profile.avatar),
            }
        except BusinessProfile.DoesNotExist:
            return {
                "company_name": None,
                "industry": None,
                "description": None,
                "website": None,
                "goals": [],
                "key_metrics": {},
                "has_avatar": False,
            }
    
    def _get_usage_summary(self) -> Dict[str, int]:
        """Get usage statistics summary."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        return {
            "total_conversations": Conversation.objects.filter(
                user=self.user
            ).count(),
            "conversations_last_30d": Conversation.objects.filter(
                user=self.user, updated_at__gte=thirty_days_ago
            ).count(),
            "total_messages": Message.objects.filter(
                conversation__user=self.user
            ).count(),
            "total_documents": Document.objects.filter(
                uploaded_by=self.user
            ).count(),
            "total_tasks": Task.objects.filter(
                Q(created_by=self.user) | Q(assignee=self.user)
            ).count(),
            "completed_tasks": Task.objects.filter(
                Q(created_by=self.user) | Q(assignee=self.user),
                status="completed"
            ).count(),
            "pending_tasks": Task.objects.filter(
                Q(created_by=self.user) | Q(assignee=self.user),
                status__in=["pending", "in_progress"]
            ).count(),
        }
    
    def _generate_insights(self) -> Dict[str, Any]:
        """Generate AI-powered insights from user activity."""
        # Get top conversation topics from message content
        recent_messages = Message.objects.filter(
            conversation__user=self.user,
            role="user",
            created_at__gte=datetime.now() - timedelta(days=30)
        ).values_list("content", flat=True)[:100]
        
        # Extract keywords/topics (simple approach)
        topics = self._extract_topics(recent_messages)
        
        # Get suggested focus areas based on task status
        focus_areas = self._suggest_focus_areas()
        
        # Calculate engagement metrics
        engagement = self._calculate_engagement()
        
        return {
            "top_topics": topics[:10],
            "suggested_focus_areas": focus_areas,
            "engagement_metrics": engagement,
            "productivity_score": self._calculate_productivity_score(),
        }
    
    def _extract_topics(self, messages: List[str]) -> List[Dict[str, Any]]:
        """Extract common topics from messages."""
        # Define business-related keywords
        business_keywords = {
            "revenue": ["revenue", "sales", "income", "profit", "money", "earnings"],
            "marketing": ["marketing", "campaign", "ads", "advertising", "promotion"],
            "product": ["product", "feature", "development", "roadmap", "launch"],
            "customer": ["customer", "client", "support", "service", "satisfaction"],
            "team": ["team", "hiring", "employee", "staff", "management"],
            "strategy": ["strategy", "plan", "goal", "objective", "vision"],
            "operations": ["operations", "process", "workflow", "efficiency"],
            "finance": ["finance", "budget", "accounting", "tax", "investment"],
            "technology": ["technology", "software", "tools", "automation", "ai"],
            "legal": ["legal", "contract", "compliance", "regulation", "law"],
        }
        
        topic_counts = Counter()
        
        for message in messages:
            message_lower = message.lower()
            for topic, keywords in business_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    topic_counts[topic] += 1
        
        # Convert to list of dicts
        return [
            {"topic": topic.replace("_", " ").title(), "frequency": count}
            for topic, count in topic_counts.most_common(10)
        ]
    
    def _suggest_focus_areas(self) -> List[str]:
        """Suggest focus areas based on user's task and conversation patterns."""
        suggestions = []
        
        # Check for overdue tasks
        overdue_count = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user),
            status__in=["pending", "in_progress"],
            due_date__lt=datetime.now(),
        ).count()
        
        if overdue_count > 0:
            suggestions.append(f"Address {overdue_count} overdue task(s)")
        
        # Check for high priority pending tasks
        high_priority_count = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user),
            priority="high",
            status__in=["pending", "in_progress"],
        ).count()
        
        if high_priority_count > 0:
            suggestions.append(f"Complete {high_priority_count} high priority task(s)")
        
        # Check for unused documents
        unprocessed_docs = Document.objects.filter(
            uploaded_by=self.user,
            processing_status="pending",
        ).count()
        
        if unprocessed_docs > 0:
            suggestions.append(f"Process {unprocessed_docs} pending document(s)")
        
        # Check conversation activity
        week_ago = datetime.now() - timedelta(days=7)
        recent_conversations = Conversation.objects.filter(
            user=self.user,
            updated_at__gte=week_ago,
        ).count()
        
        if recent_conversations < 3:
            suggestions.append("Start more conversations with Aiden to get insights")
        
        return suggestions if suggestions else ["You're all caught up! Great job!"]
    
    def _calculate_engagement(self) -> Dict[str, Any]:
        """Calculate user engagement metrics."""
        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=30)
        
        # Weekly activity
        weekly_messages = Message.objects.filter(
            conversation__user=self.user,
            created_at__gte=week_ago
        ).count()
        
        # Monthly activity
        monthly_messages = Message.objects.filter(
            conversation__user=self.user,
            created_at__gte=month_ago
        ).count()
        
        # Average messages per conversation
        avg_messages = 0
        convo_count = Conversation.objects.filter(user=self.user).count()
        if convo_count > 0:
            total_messages = Message.objects.filter(conversation__user=self.user).count()
            avg_messages = round(total_messages / convo_count, 1)
        
        return {
            "messages_this_week": weekly_messages,
            "messages_this_month": monthly_messages,
            "avg_messages_per_conversation": avg_messages,
            "active_days_last_30d": self._count_active_days(),
        }
    
    def _count_active_days(self) -> int:
        """Count unique active days in last 30 days."""
        month_ago = datetime.now() - timedelta(days=30)
        
        # Get distinct dates from message creation
        active_dates = Message.objects.filter(
            conversation__user=self.user,
            created_at__gte=month_ago
        ).dates("created_at", "day")
        
        return len(active_dates)
    
    def _calculate_productivity_score(self) -> int:
        """Calculate a productivity score (0-100)."""
        score = 50  # Base score
        
        # Task completion rate
        total_tasks = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user),
        ).count()
        
        if total_tasks > 0:
            completed = Task.objects.filter(
                Q(created_by=self.user) | Q(assignee=self.user),
                status="completed",
                ).count()
            completion_rate = completed / total_tasks
            score += int(completion_rate * 25)
        
        # Activity bonus
        month_ago = datetime.now() - timedelta(days=30)
        monthly_messages = Message.objects.filter(
            conversation__user=self.user,
            created_at__gte=month_ago
        ).count()
        
        if monthly_messages > 50:
            score += 15
        elif monthly_messages > 20:
            score += 10
        elif monthly_messages > 5:
            score += 5
        
        # Document processing
        processed_docs = Document.objects.filter(
            uploaded_by=self.user,
            processing_status="completed",
        ).count()
        
        if processed_docs > 5:
            score += 10
        elif processed_docs > 0:
            score += 5
        
        return min(100, score)
    
    def _get_activity_trends(self) -> List[Dict[str, Any]]:
        """Get daily activity trends for the last 30 days."""
        trends = []
        today = datetime.now().date()
        
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            message_count = Message.objects.filter(
                conversation__user=self.user,
                created_at__date=date
            ).count()
            
            trends.append({
                "date": date.isoformat(),
                "messages": message_count,
            })
        
        return trends
    
    def _get_followups(self) -> List[str]:
        """Get pending follow-ups and reminders."""
        followups = []
        
        # Overdue tasks
        overdue = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user),
            status__in=["pending", "in_progress"],
            due_date__lt=datetime.now(),
        ).order_by("due_date")[:3]
        
        for task in overdue:
            followups.append(f"Overdue: {task.title}")
        
        # High priority tasks
        high_priority = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user),
            priority="high",
            status__in=["pending", "in_progress"],
        ).exclude(
            id__in=[t.id for t in overdue]
        ).order_by("due_date")[:3]
        
        for task in high_priority:
            followups.append(f"High priority: {task.title}")
        
        # Unread conversations (if we had read status)
        week_ago = datetime.now() - timedelta(days=7)
        old_conversations = Conversation.objects.filter(
            user=self.user,
            updated_at__lt=week_ago,
        ).order_by("-updated_at")[:2]
        
        for convo in old_conversations:
            followups.append(f"Follow up on: {convo.title}")
        
        return followups if followups else ["No pending follow-ups"]
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity feed."""
        activities = []
        
        # Recent messages
        recent_messages = Message.objects.filter(
            conversation__user=self.user
        ).select_related("conversation").order_by("-created_at")[:10]
        
        for msg in recent_messages:
            activities.append({
                "type": "message",
                "description": f"{'Sent' if msg.role == 'user' else 'Received'} message in {msg.conversation.title[:30]}",
                "timestamp": msg.created_at.isoformat(),
                "icon": "message",
            })
        
        # Recent task activities
        recent_tasks = TaskActivity.objects.filter(
            task__created_by=self.user
        ).select_related("task").order_by("-created_at")[:10]
        
        for activity in recent_tasks:
            activities.append({
                "type": "task",
                "description": f"{activity.activity_type}: {activity.task.title[:30]}",
                "timestamp": activity.created_at.isoformat(),
                "icon": "task",
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activities[:15]

    def track_activity(self, event_type: str, feature: str, metadata: Dict[str, Any] = None) -> None:
        """Track a user activity event."""
        from core.models_analytics import UserActivity
        
        UserActivity.objects.create(
            user=self.user,
            workspace_id=metadata.get('workspace_id') if metadata else None,
            event_type=event_type,
            feature=feature,
            metadata=metadata or {}
        )
    
    def get_user_engagement(self, days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics."""
        from django.db.models import Count
        from core.models_analytics import UserActivity, FeatureUsage
        from datetime import datetime, timedelta
        
        since = datetime.now() - timedelta(days=days)
        
        # Activity counts by feature
        feature_usage = (
            UserActivity.objects.filter(
                user=self.user,
                created_at__gte=since
            )
            .values('feature')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Daily active usage
        daily_activity = (
            UserActivity.objects.filter(
                user=self.user,
                created_at__gte=since
            )
            .extra({'date': "date(created_at)"})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        total_actions = sum(f['count'] for f in feature_usage)
        active_days = len(set(a['date'] for a in daily_activity))
        
        return {
            'period_days': days,
            'total_actions': total_actions,
            'active_days': active_days,
            'feature_breakdown': list(feature_usage),
            'daily_activity': list(daily_activity),
            'engagement_score': min(100, (active_days / days) * 100 + (total_actions / 100))
        }
    
    def get_ai_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get AI usage and cost metrics."""
        from django.db.models import Sum, Avg, Count
        from core.models_analytics import AIMetrics
        from datetime import datetime, timedelta
        
        since = datetime.now() - timedelta(days=days)
        
        metrics = AIMetrics.objects.filter(
            user=self.user,
            created_at__gte=since
        )
        
        total_calls = metrics.count()
        if total_calls == 0:
            return {
                'period_days': days,
                'total_calls': 0,
                'total_tokens': 0,
                'total_cost': 0,
                'avg_response_time': 0,
                'success_rate': 0,
                'by_model': [],
                'by_operation': []
            }
        
        by_model = (
            metrics.values('model')
            .annotate(
                calls=Count('id'),
                tokens=Sum('total_tokens'),
                cost=Sum('cost_usd'),
                avg_time=Avg('response_time_ms')
            )
            .order_by('-calls')
        )
        
        by_operation = (
            metrics.values('operation')
            .annotate(
                calls=Count('id'),
                tokens=Sum('total_tokens')
            )
            .order_by('-calls')
        )
        
        success_rate = (
            metrics.filter(success=True).count() / total_calls * 100
        )
        
        return {
            'period_days': days,
            'total_calls': total_calls,
            'total_tokens': metrics.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0,
            'total_cost': float(metrics.aggregate(Sum('cost_usd'))['cost_usd__sum'] or 0),
            'avg_response_time': metrics.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0,
            'success_rate': round(success_rate, 2),
            'by_model': list(by_model),
            'by_operation': list(by_operation)
        }
