"""
Analytics WebSocket Service for real-time analytics data.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.database import get_db_session
from app.models.integration import Integration, IntegrationStatus
from app.models.tool_execution import ToolExecution
from app.core.logging import get_logger

logger = get_logger(__name__)

class AnalyticsWebSocketService:
    """Service for providing real-time analytics data via WebSocket."""
    
    async def get_user_analytics_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics summary for a user."""
        try:
            with get_db_session() as db:
                # Get user's integrations
                integrations = db.query(Integration).filter(
                    Integration.owner_id == user_id
                ).all()
                
                if not integrations:
                    return {
                        "total_integrations": 0,
                        "active_integrations": 0,
                        "total_calls_24h": 0,
                        "success_rate_24h": 0,
                        "avg_response_time_ms": 0,
                        "integrations": []
                    }
                
                integration_ids = [i.id for i in integrations]
                last_24h = datetime.utcnow() - timedelta(hours=24)
                
                # Get 24h metrics
                total_calls_24h = db.query(ToolExecution).filter(
                    ToolExecution.integration_id.in_(integration_ids),
                    ToolExecution.started_at >= last_24h
                ).count()
                
                successful_calls_24h = db.query(ToolExecution).filter(
                    ToolExecution.integration_id.in_(integration_ids),
                    ToolExecution.started_at >= last_24h,
                    ToolExecution.success == True
                ).count()
                
                avg_response_time = db.query(func.avg(ToolExecution.execution_time)).filter(
                    ToolExecution.integration_id.in_(integration_ids),
                    ToolExecution.started_at >= last_24h,
                    ToolExecution.success == True
                ).scalar() or 0.0
                
                # Integration summaries
                integration_summaries = []
                for integration in integrations:
                    calls_24h = db.query(ToolExecution).filter(
                        ToolExecution.integration_id == integration.id,
                        ToolExecution.started_at >= last_24h
                    ).count()
                    
                    successful_calls = db.query(ToolExecution).filter(
                        ToolExecution.integration_id == integration.id,
                        ToolExecution.started_at >= last_24h,
                        ToolExecution.success == True
                    ).count()
                    
                    integration_summaries.append({
                        "id": integration.id,
                        "name": integration.name,
                        "type": integration.integration_type.value,
                        "status": integration.status.value,
                        "health_status": integration.health_status or "unknown",
                        "calls_24h": calls_24h,
                        "success_rate": (successful_calls / calls_24h * 100) if calls_24h > 0 else 0
                    })
                
                return {
                    "total_integrations": len(integrations),
                    "active_integrations": len([i for i in integrations if i.status == IntegrationStatus.ACTIVE]),
                    "total_calls_24h": total_calls_24h,
                    "successful_calls_24h": successful_calls_24h,
                    "success_rate_24h": (successful_calls_24h / total_calls_24h * 100) if total_calls_24h > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time * 1000, 2),
                    "integrations": integration_summaries
                }
                
        except Exception as e:
            logger.error(f"Failed to get user analytics summary: {e}")
            return {
                "error": "Failed to load analytics data",
                "total_integrations": 0,
                "active_integrations": 0,
                "total_calls_24h": 0,
                "success_rate_24h": 0,
                "avg_response_time_ms": 0,
                "integrations": []
            }
    
    async def get_integration_analytics(self, user_id: int, integration_id: int) -> Dict[str, Any]:
        """Get detailed analytics for a specific integration."""
        try:
            with get_db_session() as db:
                # Verify integration ownership
                integration = db.query(Integration).filter(
                    Integration.id == integration_id,
                    Integration.owner_id == user_id
                ).first()
                
                if not integration:
                    return {"error": "Integration not found"}
                
                # Get recent activity (last 24 hours)
                last_24h = datetime.utcnow() - timedelta(hours=24)
                
                recent_executions = db.query(ToolExecution).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= last_24h
                ).order_by(desc(ToolExecution.started_at)).limit(10).all()
                
                # Tool usage breakdown
                tool_usage = db.query(
                    ToolExecution.tool_name,
                    func.count().label('total_calls'),
                    func.sum(func.case([(ToolExecution.success == True, 1)], else_=0)).label('successful_calls')
                ).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= last_24h
                ).group_by(ToolExecution.tool_name).all()
                
                return {
                    "integration_id": integration_id,
                    "integration_name": integration.name,
                    "integration_type": integration.integration_type.value,
                    "status": integration.status.value,
                    "health_status": integration.health_status or "unknown",
                    "recent_executions": [
                        {
                            "timestamp": exec.started_at.isoformat(),
                            "tool_name": exec.tool_name,
                            "success": exec.success,
                            "response_time_ms": round(exec.execution_time * 1000, 2) if exec.execution_time else 0,
                            "error_message": exec.error_message if not exec.success else None
                        }
                        for exec in recent_executions
                    ],
                    "tool_usage": [
                        {
                            "tool_name": usage.tool_name,
                            "total_calls": usage.total_calls,
                            "successful_calls": usage.successful_calls,
                            "success_rate": (usage.successful_calls / usage.total_calls * 100) if usage.total_calls > 0 else 0
                        }
                        for usage in tool_usage
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get integration analytics: {e}")
            return {"error": "Failed to load integration analytics"}
    
    async def get_live_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get live metrics for real-time updates."""
        try:
            with get_db_session() as db:
                # Get very recent activity (last 5 minutes)
                last_5min = datetime.utcnow() - timedelta(minutes=5)
                
                integrations = db.query(Integration).filter(
                    Integration.owner_id == user_id
                ).all()
                
                integration_ids = [i.id for i in integrations]
                
                recent_calls = db.query(ToolExecution).filter(
                    ToolExecution.integration_id.in_(integration_ids),
                    ToolExecution.started_at >= last_5min
                ).count()
                
                recent_errors = db.query(ToolExecution).filter(
                    ToolExecution.integration_id.in_(integration_ids),
                    ToolExecution.started_at >= last_5min,
                    ToolExecution.success == False
                ).count()
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "recent_calls_5min": recent_calls,
                    "recent_errors_5min": recent_errors,
                    "active_integrations": len([i for i in integrations if i.status == IntegrationStatus.ACTIVE])
                }
                
        except Exception as e:
            logger.error(f"Failed to get live metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "recent_calls_5min": 0,
                "recent_errors_5min": 0,
                "active_integrations": 0,
                "error": "Failed to load live metrics"
            }

# Global service instance
analytics_websocket_service = AnalyticsWebSocketService()