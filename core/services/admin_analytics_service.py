"""Admin Analytics Service - Workspace and admin-level metrics."""
from typing import Dict, Any, List, Optional
from django.db.models import Count, Sum, Avg
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()


class AdminAnalyticsService:
    """Service for admin and workspace analytics."""

    def __init__(self, user: User):
        self.user = user

    def get_workspace_analytics(
        self,
        workspace_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a specific workspace."""
        from core.models_analytics import UserActivity, AIMetrics
        from core.models import WorkspaceMember
        
        since = datetime.now() - timedelta(days=days)
        
        # Member activity
        member_activities = (
            UserActivity.objects.filter(
                workspace_id=workspace_id,
                created_at__gte=since
            )
            .values('user__email')
            .annotate(
                actions=Count('id'),
                features_used=Count('feature', distinct=True)
            )
            .order_by('-actions')[:10]
        )
        
        # Feature usage breakdown
        feature_usage = (
            UserActivity.objects.filter(
                workspace_id=workspace_id,
                created_at__gte=since
            )
            .values('feature')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # AI usage
        ai_usage = (
            AIMetrics.objects.filter(
                workspace_id=workspace_id,
                created_at__gte=since
            )
            .aggregate(
                total_calls=Count('id'),
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('cost_usd'),
                avg_response_time=Avg('response_time_ms'),
            )
        )
        
        # Active members count
        active_members = (
            UserActivity.objects.filter(
                workspace_id=workspace_id,
                created_at__gte=since
            )
            .values('user')
            .distinct()
            .count()
        )
        
        total_members = WorkspaceMember.objects.filter(
            workspace_id=workspace_id
        ).count()
        
        return {
            'period_days': days,
            'workspace_id': workspace_id,
            'active_members': active_members,
            'total_members': total_members,
            'engagement_rate': round(active_members / total_members * 100, 2) if total_members > 0 else 0,
            'top_contributors': list(member_activities),
            'feature_breakdown': list(feature_usage),
            'ai_usage': {
                'total_calls': ai_usage['total_calls'] or 0,
                'total_tokens': ai_usage['total_tokens'] or 0,
                'total_cost': float(ai_usage['total_cost'] or 0),
                'avg_response_time': round(ai_usage['avg_response_time'] or 0, 2),
            }
        }

    def get_admin_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """Get admin dashboard metrics (requires superuser)."""
        from core.models_analytics import UserActivity, AIMetrics, RetentionSnapshot
        from core.models import User, Workspace
        
        if not self.user.is_staff:
            return {'error': 'Admin access required'}
        
        since = datetime.now() - timedelta(days=days)
        
        # User metrics
        total_users = User.objects.count()
        new_users = User.objects.filter(
            date_joined__gte=since
        ).count()
        
        # Active users
        active_users = (
            UserActivity.objects.filter(
                created_at__gte=since
            )
            .values('user')
            .distinct()
            .count()
        )
        
        # Workspace metrics
        total_workspaces = Workspace.objects.count()
        active_workspaces = (
            UserActivity.objects.filter(
                created_at__gte=since,
                workspace__isnull=False
            )
            .values('workspace')
            .distinct()
            .count()
        )
        
        # AI metrics across platform
        ai_metrics = (
            AIMetrics.objects.filter(
                created_at__gte=since
            )
            .aggregate(
                total_calls=Count('id'),
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('cost_usd'),
                avg_response_time=Avg('response_time_ms'),
            )
        )
        
        # Top features
        top_features = (
            UserActivity.objects.filter(
                created_at__gte=since
            )
            .values('feature')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Daily active users trend
        daily_active = (
            UserActivity.objects.filter(
                created_at__gte=since
            )
            .extra({'date': "date(created_at)"})
            .values('date')
            .annotate(active_users=Count('user', distinct=True))
            .order_by('date')
        )
        
        return {
            'period_days': days,
            'users': {
                'total': total_users,
                'new': new_users,
                'active': active_users,
                'retention_rate': round(active_users / total_users * 100, 2) if total_users > 0 else 0,
            },
            'workspaces': {
                'total': total_workspaces,
                'active': active_workspaces,
            },
            'ai': {
                'total_calls': ai_metrics['total_calls'] or 0,
                'total_tokens': ai_metrics['total_tokens'] or 0,
                'total_cost': float(ai_metrics['total_cost'] or 0),
                'avg_response_time': round(ai_metrics['avg_response_time'] or 0, 2),
            },
            'top_features': list(top_features),
            'daily_active_trend': list(daily_active),
        }

    def get_retention_report(self, cohort_days: int = 30) -> Dict[str, Any]:
        """Get user retention analysis."""
        from core.models_analytics import SessionAnalytics, UserActivity
        from core.models import User
        
        now = datetime.now()
        cohort_start = now - timedelta(days=cohort_days)
        
        # New users in cohort period
        new_users = User.objects.filter(
            date_joined__gte=cohort_start,
            date_joined__lt=now
        )
        
        new_user_ids = list(new_users.values_list('id', flat=True))
        
        if not new_user_ids:
            return {'cohort_size': 0, 'retention': {}}
        
        # Check if they returned on day 1, 7, 30
        retention = {}
        for day in [1, 7, 30]:
            check_date = cohort_start + timedelta(days=day)
            if check_date > now:
                retention[f'day_{day}'] = None
                continue
            
            active_count = (
                UserActivity.objects.filter(
                    user_id__in=new_user_ids,
                    created_at__gte=check_date,
                    created_at__lt=check_date + timedelta(days=1)
                )
                .values('user')
                .distinct()
                .count()
            )
            
            retention[f'day_{day}'] = round(
                active_count / len(new_user_ids) * 100, 2
            )
        
        return {
            'cohort_period_days': cohort_days,
            'cohort_start': cohort_start.isoformat(),
            'cohort_end': now.isoformat(),
            'cohort_size': len(new_user_ids),
            'retention': retention,
        }
