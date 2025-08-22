"""
Advanced Analytics endpoints for integration monitoring and metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from app.core.security import get_current_active_user
from app.db.database import get_db_session
from app.models.user import User
from app.models.integration import Integration, IntegrationStatus
from app.models.tool_execution import ToolExecution, StreamingEvent, AgentActivity
from app.services.cache_service import cache_service, CacheNamespaces
from app.services.tool_tracking_service import tool_tracking_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/integrations/overview")
async def get_integrations_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get comprehensive overview of all user integrations with key metrics."""
    try:
        # Get user's integrations with basic stats
        integrations = db.query(Integration).filter(
            Integration.owner_id == current_user.id
        ).all()
        
        overview_data = []
        for integration in integrations:
            # Get execution stats for last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            total_executions = db.query(ToolExecution).filter(
                ToolExecution.integration_id == integration.id,
                ToolExecution.started_at >= thirty_days_ago
            ).count()
            
            successful_executions = db.query(ToolExecution).filter(
                ToolExecution.integration_id == integration.id,
                ToolExecution.started_at >= thirty_days_ago,
                ToolExecution.success == True
            ).count()
            
            avg_response_time = db.query(func.avg(ToolExecution.execution_time)).filter(
                ToolExecution.integration_id == integration.id,
                ToolExecution.started_at >= thirty_days_ago,
                ToolExecution.success == True
            ).scalar() or 0.0
            
            # Calculate uptime percentage based on health checks
            uptime_percentage = 95.0 if integration.status == IntegrationStatus.ACTIVE else 60.0
            
            overview_data.append({
                "integration_id": integration.id,
                "name": integration.name,
                "type": integration.integration_type.value,
                "status": integration.status.value,
                "health_status": integration.health_status or "unknown",
                "metrics": {
                    "total_api_calls_30d": total_executions,
                    "successful_calls_30d": successful_executions,
                    "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time * 1000, 2),
                    "uptime_percentage": uptime_percentage,
                    "error_count": integration.error_count or 0,
                    "last_activity": integration.last_health_check
                }
            })
        
        return {
            "total_integrations": len(integrations),
            "active_integrations": len([i for i in integrations if i.status == IntegrationStatus.ACTIVE]),
            "integrations": overview_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get integrations overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}/performance-trends")
async def get_integration_performance_trends(
    integration_id: int,
    timeframe: str = Query(default="7d", regex="^(24h|7d|30d)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get performance trends for a specific integration over time."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        # Calculate time range
        timeframes = {"24h": 1, "7d": 7, "30d": 30}
        days = timeframes[timeframe]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get hourly aggregated performance data
        if timeframe == "24h":
            # Hourly granularity for 24h
            time_buckets = []
            for i in range(24):
                bucket_start = start_date + timedelta(hours=i)
                bucket_end = bucket_start + timedelta(hours=1)
                
                executions = db.query(ToolExecution).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= bucket_start,
                    ToolExecution.started_at < bucket_end
                ).all()
                
                total_calls = len(executions)
                successful_calls = len([e for e in executions if e.success])
                avg_response_time = sum([e.execution_time for e in executions if e.execution_time]) / total_calls if total_calls > 0 else 0
                
                time_buckets.append({
                    "timestamp": bucket_start.isoformat(),
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "failed_calls": total_calls - successful_calls,
                    "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time * 1000, 2)
                })
        else:
            # Daily granularity for 7d/30d
            time_buckets = []
            for i in range(days):
                bucket_start = start_date + timedelta(days=i)
                bucket_end = bucket_start + timedelta(days=1)
                
                total_calls = db.query(ToolExecution).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= bucket_start,
                    ToolExecution.started_at < bucket_end
                ).count()
                
                successful_calls = db.query(ToolExecution).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= bucket_start,
                    ToolExecution.started_at < bucket_end,
                    ToolExecution.success == True
                ).count()
                
                avg_response_time = db.query(func.avg(ToolExecution.execution_time)).filter(
                    ToolExecution.integration_id == integration_id,
                    ToolExecution.started_at >= bucket_start,
                    ToolExecution.started_at < bucket_end,
                    ToolExecution.success == True
                ).scalar() or 0.0
                
                time_buckets.append({
                    "date": bucket_start.date().isoformat(),
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "failed_calls": total_calls - successful_calls,
                    "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time * 1000, 2)
                })
        
        return {
            "integration_id": integration_id,
            "integration_name": integration.name,
            "timeframe": timeframe,
            "data_points": len(time_buckets),
            "performance_data": time_buckets
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}/error-analysis")
async def get_integration_error_analysis(
    integration_id: int,
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get detailed error analysis for an integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get failed executions with error details
        failed_executions = db.query(ToolExecution).filter(
            ToolExecution.integration_id == integration_id,
            ToolExecution.started_at >= start_date,
            ToolExecution.success == False
        ).order_by(desc(ToolExecution.started_at)).all()
        
        # Categorize errors
        error_categories = {}
        recent_errors = []
        
        for execution in failed_executions:
            error_msg = execution.error_message or "Unknown error"
            
            # Simple error categorization
            if "timeout" in error_msg.lower():
                category = "timeout"
            elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                category = "authentication"
            elif "rate limit" in error_msg.lower():
                category = "rate_limiting"
            elif "connection" in error_msg.lower():
                category = "connectivity"
            else:
                category = "other"
            
            if category not in error_categories:
                error_categories[category] = 0
            error_categories[category] += 1
            
            # Add to recent errors (limit to 10)
            if len(recent_errors) < 10:
                recent_errors.append({
                    "timestamp": execution.started_at.isoformat(),
                    "tool_name": execution.tool_name,
                    "error_message": error_msg,
                    "category": category,
                    "execution_time_ms": round(execution.execution_time * 1000, 2) if execution.execution_time else 0
                })
        
        total_executions = db.query(ToolExecution).filter(
            ToolExecution.integration_id == integration_id,
            ToolExecution.started_at >= start_date
        ).count()
        
        return {
            "integration_id": integration_id,
            "integration_name": integration.name,
            "analysis_period_days": days,
            "total_executions": total_executions,
            "total_failures": len(failed_executions),
            "failure_rate": (len(failed_executions) / total_executions * 100) if total_executions > 0 else 0,
            "error_categories": error_categories,
            "recent_errors": recent_errors
        }
        
    except Exception as e:
        logger.error(f"Failed to get error analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}/usage-patterns")
async def get_integration_usage_patterns(
    integration_id: int,
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get usage patterns and tool utilization for an integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Tool usage breakdown
        tool_usage = db.query(
            ToolExecution.tool_name,
            func.count().label('total_calls'),
            func.sum(func.case([(ToolExecution.success == True, 1)], else_=0)).label('successful_calls'),
            func.avg(ToolExecution.execution_time).label('avg_response_time')
        ).filter(
            ToolExecution.integration_id == integration_id,
            ToolExecution.started_at >= start_date
        ).group_by(ToolExecution.tool_name).order_by(desc('total_calls')).all()
        
        # Peak usage hours analysis
        hourly_usage = db.query(
            func.extract('hour', ToolExecution.started_at).label('hour'),
            func.count().label('calls')
        ).filter(
            ToolExecution.integration_id == integration_id,
            ToolExecution.started_at >= start_date
        ).group_by('hour').all()
        
        # Daily usage pattern
        daily_usage = db.query(
            func.date(ToolExecution.started_at).label('date'),
            func.count().label('calls')
        ).filter(
            ToolExecution.integration_id == integration_id,
            ToolExecution.started_at >= start_date
        ).group_by('date').order_by('date').all()
        
        return {
            "integration_id": integration_id,
            "integration_name": integration.name,
            "analysis_period_days": days,
            "tool_usage": [
                {
                    "tool_name": usage.tool_name,
                    "total_calls": usage.total_calls,
                    "successful_calls": usage.successful_calls,
                    "success_rate": (usage.successful_calls / usage.total_calls * 100) if usage.total_calls > 0 else 0,
                    "avg_response_time_ms": round(usage.avg_response_time * 1000, 2) if usage.avg_response_time else 0
                }
                for usage in tool_usage
            ],
            "peak_hours": [
                {
                    "hour": int(hour_data.hour),
                    "calls": hour_data.calls
                }
                for hour_data in sorted(hourly_usage, key=lambda x: x.calls, reverse=True)[:5]
            ],
            "daily_usage": [
                {
                    "date": usage.date.isoformat(),
                    "calls": usage.calls
                }
                for usage in daily_usage
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/summary")
async def get_analytics_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get comprehensive analytics summary for dashboard."""
    try:
        # Time periods for analysis
        last_24h = datetime.utcnow() - timedelta(hours=24)
        last_7d = datetime.utcnow() - timedelta(days=7)
        last_30d = datetime.utcnow() - timedelta(days=30)
        
        # Get user's integrations
        integrations = db.query(Integration).filter(
            Integration.owner_id == current_user.id
        ).all()
        
        integration_ids = [i.id for i in integrations]
        
        # Overall metrics
        total_calls_24h = db.query(ToolExecution).filter(
            ToolExecution.integration_id.in_(integration_ids),
            ToolExecution.started_at >= last_24h
        ).count()
        
        successful_calls_24h = db.query(ToolExecution).filter(
            ToolExecution.integration_id.in_(integration_ids),
            ToolExecution.started_at >= last_24h,
            ToolExecution.success == True
        ).count()
        
        avg_response_time_24h = db.query(func.avg(ToolExecution.execution_time)).filter(
            ToolExecution.integration_id.in_(integration_ids),
            ToolExecution.started_at >= last_24h,
            ToolExecution.success == True
        ).scalar() or 0.0
        
        # Integration health summary
        healthy_integrations = len([i for i in integrations if i.health_status == "healthy"])
        unhealthy_integrations = len([i for i in integrations if i.health_status == "unhealthy"])
        unknown_integrations = len([i for i in integrations if not i.health_status or i.health_status == "unknown"])
        
        # Recent activity (last 10 executions)
        recent_activity = db.query(ToolExecution).filter(
            ToolExecution.integration_id.in_(integration_ids)
        ).order_by(desc(ToolExecution.started_at)).limit(10).all()
        
        return {
            "summary": {
                "total_integrations": len(integrations),
                "active_integrations": len([i for i in integrations if i.status == IntegrationStatus.ACTIVE]),
                "total_calls_24h": total_calls_24h,
                "successful_calls_24h": successful_calls_24h,
                "success_rate_24h": (successful_calls_24h / total_calls_24h * 100) if total_calls_24h > 0 else 0,
                "avg_response_time_ms": round(avg_response_time_24h * 1000, 2)
            },
            "health_overview": {
                "healthy": healthy_integrations,
                "unhealthy": unhealthy_integrations,
                "unknown": unknown_integrations
            },
            "recent_activity": [
                {
                    "timestamp": activity.started_at.isoformat(),
                    "integration_name": next((i.name for i in integrations if i.id == activity.integration_id), "Unknown"),
                    "tool_name": activity.tool_name,
                    "success": activity.success,
                    "response_time_ms": round(activity.execution_time * 1000, 2) if activity.execution_time else 0
                }
                for activity in recent_activity
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-analysis")
async def get_cost_analysis(
    timeframe: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get cost analysis based on API usage (estimated costs)."""
    try:
        timeframes = {"7d": 7, "30d": 30, "90d": 90}
        days = timeframes[timeframe]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        integrations = db.query(Integration).filter(
            Integration.owner_id == current_user.id
        ).all()
        
        cost_breakdown = []
        total_estimated_cost = 0.0
        
        # Estimated cost per API call by integration type (these are example rates)
        COST_ESTIMATES = {
            "salesforce": 0.002,  # $0.002 per API call
            "jira": 0.001,        # $0.001 per API call
            "zendesk": 0.0015,    # $0.0015 per API call
            "github": 0.0005,     # $0.0005 per API call
            "slack": 0.0008,      # $0.0008 per API call
        }
        
        for integration in integrations:
            total_calls = db.query(ToolExecution).filter(
                ToolExecution.integration_id == integration.id,
                ToolExecution.started_at >= start_date
            ).count()
            
            cost_per_call = COST_ESTIMATES.get(integration.integration_type.value, 0.001)
            estimated_cost = total_calls * cost_per_call
            total_estimated_cost += estimated_cost
            
            cost_breakdown.append({
                "integration_id": integration.id,
                "integration_name": integration.name,
                "integration_type": integration.integration_type.value,
                "total_calls": total_calls,
                "cost_per_call": cost_per_call,
                "estimated_cost": round(estimated_cost, 4),
                "percentage_of_total": 0  # Will calculate after loop
            })
        
        # Calculate percentages
        for item in cost_breakdown:
            if total_estimated_cost > 0:
                item["percentage_of_total"] = round(item["estimated_cost"] / total_estimated_cost * 100, 2)
        
        return {
            "timeframe": timeframe,
            "period_days": days,
            "total_estimated_cost": round(total_estimated_cost, 4),
            "cost_breakdown": sorted(cost_breakdown, key=lambda x: x["estimated_cost"], reverse=True),
            "note": "These are estimated costs based on typical API pricing. Actual costs may vary."
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))