import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.db.models import Count, Q
from core.models import Task, Message
from services.model_layer import call_model, TaskType, Priority

logger = logging.getLogger(__name__)

def get_business_forecast(user_id: int) -> Dict[str, Any]:
    """
    Analyzes historical data to predict business trends and productivity.
    """
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # 1. Historical Velocity
    completed_tasks = Task.objects.filter(
        user_id=user_id,
        status="done",
        updated_at__gte=thirty_days_ago
    ).count()
    
    weekly_velocity = completed_tasks / 4.0
    
    # 2. Backlog Pressure
    pending_tasks = Task.objects.filter(
        user_id=user_id,
        status__in=["todo", "in_progress", "review"]
    ).count()
    
    estimated_days_to_clear = (pending_tasks / weekly_velocity * 7) if weekly_velocity > 0 else (pending_tasks * 2) # fallback
    
    # 3. AI Interpretation
    try:
        data_summary = f"""
        Stats for the last 30 days:
        - Tasks Completed: {completed_tasks}
        - Current Backlog: {pending_tasks}
        - Weekly Throughput: {weekly_velocity:.1f} tasks/week
        - Est. Days to Clear Backlog: {estimated_days_to_clear:.1f}
        """
        
        prompt = f"""Based on the following business productivity data, provide a 1-sentence forecast for the next 30 days.
        Data: {data_summary}
        
        Focus on: Growth, Risk of burnout, or Capacity for new projects.
        """
        
        ai_response = call_model(
            user_id=user_id,
            user_message=prompt,
            base_system_prompt="You are a strategic business forecaster.",
            task_type=TaskType.QUICK,
            priority=Priority.NORMAL,
            use_cache=True
        )
        prediction = ai_response.text.strip().strip('"')
    except Exception as e:
        logger.error(f"Forecasting AI error: {e}")
        prediction = "Momentum is steady. Maintain current focus to clear pending items."

    return {
        "velocity": round(weekly_velocity, 1),
        "backlog_clearance_days": round(estimated_days_to_clear, 1),
        "forecast_summary": prediction,
        "trend": "up" if weekly_velocity > 2 else "stable",
        "next_30_days_capacity": int(weekly_velocity * 4)
    }
