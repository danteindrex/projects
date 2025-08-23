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
from app.models.integration import Integration
from app.services.integration_service import integration_service
from sqlalchemy.orm import Session
from app.api.deps import get_db
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

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

# Import PlainTextResponse for Prometheus endpoint
from fastapi.responses import PlainTextResponse

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

# Import time for metrics
import time

# Integration Monitoring Endpoints
active_monitoring_connections: Dict[str, WebSocket] = {}

@router.get("/integrations/activity")
async def get_integration_activity(
    limit: int = Query(default=100, ge=1, le=1000),
    integration_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get recent integration activity events"""
    try:
        # Get cached integration events from Kafka
        cache_key = f"integration_activity_{integration_id}" if integration_id else "integration_activity_all"
        cached_events = await cache_service.get(CacheNamespaces.INTEGRATION_DATA, cache_key)
        
        if cached_events:
            return {"events": cached_events[-limit:], "total": len(cached_events)}
        else:
            return {"events": [], "total": 0}
    
    except Exception as e:
        logger.error(f"Failed to get integration activity: {e}")
        return {"events": [], "total": 0, "error": str(e)}

@router.get("/integrations/{integration_id}/metrics")
async def get_integration_metrics(
    integration_id: int,
    timeframe: str = Query(default="1h", regex="^(1h|24h|7d)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics for a specific integration"""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        metrics_key = f"metrics_{integration_id}_{timeframe}"
        cached_metrics = await cache_service.get(CacheNamespaces.INTEGRATION_DATA, metrics_key)
        
        if cached_metrics:
            return cached_metrics
        else:
            # Return default metrics structure
            return {
                "integration_id": integration_id,
                "integration_name": integration.name,
                "integration_type": integration.integration_type.value,
                "timeframe": timeframe,
                "api_calls": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "rate_limited": 0
                },
                "performance": {
                    "avg_response_time_ms": 0,
                    "min_response_time_ms": 0,
                    "max_response_time_ms": 0,
                    "p95_response_time_ms": 0
                },
                "errors": [],
                "health_status": integration.health_status or "unknown"
            }
    
    except Exception as e:
        logger.error(f"Failed to get integration metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/{integration_id}/test")
async def trigger_integration_test(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a test of an integration (generates monitoring events)"""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        # Test the integration - this will generate Kafka events automatically
        success, message = await integration_service.test_integration_connection(integration)
        
        return {
            "integration_id": integration_id,
            "integration_name": integration.name,
            "test_successful": success,
            "message": message,
            "note": "Check Kafka UI at http://localhost:8080 for real-time events"
        }
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kafka/topics")
async def list_kafka_topics(current_user: User = Depends(get_current_user)):
    """List available Kafka topics for monitoring"""
    from app.core.config import settings
    
    return {
        "topics": [
            f"{settings.KAFKA_TOPIC_PREFIX}.integrations",
            f"{settings.KAFKA_TOPIC_PREFIX}.chat", 
            f"{settings.KAFKA_TOPIC_PREFIX}.agents",
            f"{settings.KAFKA_TOPIC_PREFIX}.system"
        ],
        "kafka_ui_url": "http://localhost:8080",
        "note": "Integration events are streamed to the integrations topic"
    }

@router.websocket("/integrations/realtime")
async def websocket_integration_monitoring(websocket: WebSocket):
    """Real-time integration monitoring WebSocket endpoint"""
    
    await websocket.accept()
    connection_id = f"integration_monitor_{id(websocket)}"
    active_monitoring_connections[connection_id] = websocket
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Real-time integration monitoring connected",
            "connection_id": connection_id,
            "note": "You will receive live integration events here"
        }))
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Send periodic health check
                await websocket.send_text(json.dumps({
                    "type": "health_check",
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_integrations": "Check /integrations endpoint for current status"
                }))
                
                await asyncio.sleep(10)  # Send update every 10 seconds
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket monitoring error: {e}")
                await asyncio.sleep(1)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket integration monitoring disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket integration monitoring error: {e}")
    finally:
        # Clean up connection
        if connection_id in active_monitoring_connections:
            del active_monitoring_connections[connection_id]

@router.get("/integrations/summary")
async def get_integrations_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of all integrations and their health status"""
    
    try:
        # Get user's integrations
        integrations = db.query(Integration).filter(
            Integration.owner_id == current_user.id
        ).all()
        
        summary = {
            "total_integrations": len(integrations),
            "healthy": 0,
            "unhealthy": 0,
            "unknown": 0,
            "integrations": []
        }
        
        for integration in integrations:
            status = integration.health_status or "unknown"
            summary[status] += 1
            
            summary["integrations"].append({
                "id": integration.id,
                "name": integration.name,
                "type": integration.integration_type.value,
                "status": status,
                "last_health_check": integration.last_health_check,
                "error_count": integration.error_count or 0,
                "last_error": integration.last_error
            })
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get integrations summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))