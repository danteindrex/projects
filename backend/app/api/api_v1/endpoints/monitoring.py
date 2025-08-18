"""
Monitoring and health check endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.services.monitoring_service import (
    metrics_collector, 
    health_checker, 
    alert_manager
)
from app.services.cache_service import cache_service, CacheNamespaces
from app.core.logging import get_logger
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components"""
    try:
        health_status = await health_checker.get_overall_health()
        return health_status
    except Exception as e:
        logger.error("Error getting detailed health", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/metrics")
async def get_system_metrics():
    """Get current system metrics"""
    try:
        metrics = await metrics_collector.collect_system_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_used": metrics.memory_used,
            "memory_available": metrics.memory_available,
            "disk_percent": metrics.disk_percent,
            "disk_used": metrics.disk_used,
            "disk_free": metrics.disk_free,
            "active_connections": metrics.active_connections,
            "request_count": metrics.request_count,
            "error_count": metrics.error_count,
            "avg_response_time": metrics.avg_response_time,
            "uptime_seconds": metrics.timestamp.timestamp() - metrics_collector.start_time
        }
    except Exception as e:
        logger.error("Error getting system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics collection failed")

@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to retrieve")
):
    """Get historical metrics data"""
    try:
        # Get recent metrics from collector's history
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_percent": m.disk_percent,
                "avg_response_time": m.avg_response_time,
                "request_count": m.request_count,
                "error_count": m.error_count
            }
            for m in metrics_collector.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "metrics": recent_metrics
        }
    except Exception as e:
        logger.error("Error getting metrics history", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics history retrieval failed")

@router.get("/alerts")
async def get_active_alerts():
    """Get current active alerts"""
    try:
        active_alerts = list(alert_manager.alert_history)[-10:]  # Last 10 alerts
        
        return {
            "active_alerts": len(alert_manager.active_alerts),
            "total_alert_history": len(alert_manager.alert_history),
            "recent_alerts": active_alerts
        }
    except Exception as e:
        logger.error("Error getting alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Alert retrieval failed")

@router.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Get Redis cache statistics (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        stats = await cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Cache stats retrieval failed")

@router.post("/cache/clear")
async def clear_cache(
    namespace: Optional[str] = Query(None, description="Specific namespace to clear"),
    current_user: User = Depends(get_current_user)
):
    """Clear cache (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if namespace:
            cleared_count = await cache_service.invalidate_namespace(namespace)
            logger.info("Cache namespace cleared", namespace=namespace, count=cleared_count)
            return {"message": f"Cleared {cleared_count} keys from namespace '{namespace}'"}
        else:
            # Clear all cache keys (be careful!)
            all_namespaces = [
                CacheNamespaces.USER_DATA,
                CacheNamespaces.INTEGRATION_TEMPLATES,
                CacheNamespaces.INTEGRATION_HEALTH,
                CacheNamespaces.CHAT_SESSIONS,
                CacheNamespaces.API_RESPONSES,
                CacheNamespaces.SYSTEM_CONFIG
            ]
            
            total_cleared = 0
            for ns in all_namespaces:
                cleared_count = await cache_service.invalidate_namespace(ns)
                total_cleared += cleared_count
            
            logger.info("All cache cleared", total_count=total_cleared)
            return {"message": f"Cleared {total_cleared} total cache keys"}
            
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(status_code=500, detail="Cache clear operation failed")

@router.get("/status/summary")
async def get_status_summary():
    """Get a comprehensive status summary"""
    try:
        # Get latest cached data to avoid expensive operations
        metrics = await cache_service.get(CacheNamespaces.SYSTEM_CONFIG, "latest_metrics")
        
        # Get health status
        health_components = {}
        for component in ["database", "redis", "system_resources", "integrations"]:
            health_data = await cache_service.get(CacheNamespaces.SYSTEM_CONFIG, f"health_{component}")
            if health_data:
                health_components[component] = health_data
        
        # Determine overall status
        overall_status = "healthy"
        for component_data in health_components.values():
            if component_data["status"] == "unhealthy":
                overall_status = "unhealthy"
                break
            elif component_data["status"] == "degraded" and overall_status != "unhealthy":
                overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": metrics,
            "health_components": health_components,
            "active_alerts": len(alert_manager.active_alerts),
            "uptime_seconds": time.time() - metrics_collector.start_time if metrics else 0
        }
        
    except Exception as e:
        logger.error("Error getting status summary", error=str(e))
        # Return basic status if detailed check fails
        return {
            "overall_status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Status check failed"
        }

# Endpoint for Prometheus-style metrics (simple text format)
@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        metrics = await metrics_collector.collect_system_metrics()
        
        # Format as Prometheus metrics
        prometheus_output = f"""# HELP system_cpu_percent Current CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {metrics.cpu_percent}

# HELP system_memory_percent Current memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {metrics.memory_percent}

# HELP system_disk_percent Current disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {metrics.disk_percent}

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total {metrics.request_count}

# HELP http_request_duration_seconds Average HTTP request duration
# TYPE http_request_duration_seconds gauge
http_request_duration_seconds {metrics.avg_response_time}

# HELP system_active_connections Current active connections
# TYPE system_active_connections gauge
system_active_connections {metrics.active_connections}
"""
        
        return prometheus_output
        
    except Exception as e:
        logger.error("Error generating Prometheus metrics", error=str(e))
        return "# Error generating metrics\n"

# Import PlainTextResponse for Prometheus endpoint
import time
from fastapi.responses import PlainTextResponse