"""
Real-time analytics WebSocket service for streaming analytics data updates.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.user import User
from app.models.integration import Integration, IntegrationStatus
from app.models.tool_execution import ToolExecution, StreamingEvent, AgentActivity
from app.models.analytics_metrics import AnalyticsMetrics
from app.services.cache_service import cache_service, CacheNamespaces
from app.db.database import get_db_session
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsEvent:
    """Analytics event types for real-time streaming."""
    METRICS_UPDATE = "metrics_update"
    INTEGRATION_STATUS = "integration_status"
    TOOL_EXECUTION = "tool_execution"
    PERFORMANCE_DATA = "performance_data"
    ERROR_ALERT = "error_alert"
    SYSTEM_HEALTH = "system_health"
    COST_UPDATE = "cost_update"


class AnalyticsWebSocketManager:
    """Manage WebSocket connections for real-time analytics streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> {connection_ids}
        self.subscription_filters: Dict[str, Dict[str, Any]] = {}  # connection_id -> filters
        self.analytics_task_running = False
        self.background_task = None
        
    async def connect(self, websocket: WebSocket, user_id: str, filters: Dict[str, Any] = None) -> str:
        """Connect a WebSocket client for analytics streaming."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        self.active_connections[connection_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Store subscription filters
        self.subscription_filters[connection_id] = filters or {}
        
        logger.info(f"Analytics WebSocket connected: {connection_id} for user {user_id}")
        
        # Start background analytics task if not running
        if not self.analytics_task_running:
            self.background_task = asyncio.create_task(self._analytics_streaming_task())
        
        # Send initial data
        await self._send_initial_analytics_data(connection_id, user_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: str = None):
        """Disconnect a WebSocket client."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if connection_id in self.subscription_filters:
            del self.subscription_filters[connection_id]
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"Analytics WebSocket disconnected: {connection_id}")
        
        # Stop background task if no connections
        if not self.active_connections and self.background_task:
            self.background_task.cancel()
            self.analytics_task_running = False
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to analytics connection {connection_id}: {e}")
                # Find user_id for cleanup
                user_id = None
                for uid, conn_ids in self.user_connections.items():
                    if connection_id in conn_ids:
                        user_id = uid
                        break
                self.disconnect(connection_id, user_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a user."""
        if user_id in self.user_connections:
            for connection_id in list(self.user_connections[user_id]):
                await self.send_to_connection(connection_id, message)
    
    async def broadcast_to_all(self, message: Dict[str, Any], event_type: str = None):
        """Broadcast message to all connected clients with optional filtering."""
        disconnected_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                # Apply filters if specified
                if event_type and self._should_send_to_connection(connection_id, event_type, message):
                    await websocket.send_text(json.dumps(message))
                elif not event_type:
                    await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to connection {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            # Find user_id for cleanup
            user_id = None
            for uid, conn_ids in self.user_connections.items():
                if connection_id in conn_ids:
                    user_id = uid
                    break
            self.disconnect(connection_id, user_id)
    
    def _should_send_to_connection(self, connection_id: str, event_type: str, message: Dict[str, Any]) -> bool:
        """Check if message should be sent to connection based on filters."""
        filters = self.subscription_filters.get(connection_id, {})
        
        # No filters means send all
        if not filters:
            return True
        
        # Check event type filter
        if "event_types" in filters and event_type not in filters["event_types"]:
            return False
        
        # Check integration filter
        if "integration_ids" in filters:
            integration_id = message.get("integration_id")
            if integration_id and integration_id not in filters["integration_ids"]:
                return False
        
        return True
    
    async def _send_initial_analytics_data(self, connection_id: str, user_id: str):
        """Send initial analytics data when connection is established."""
        try:
            db = next(get_db_session())
            
            # Get user's integrations overview
            integrations = db.query(Integration).filter(
                Integration.owner_id == user_id
            ).all()
            
            # Calculate basic metrics
            last_24h = datetime.utcnow() - timedelta(hours=24)
            total_calls_24h = db.query(ToolExecution).filter(
                ToolExecution.integration_id.in_([i.id for i in integrations]),
                ToolExecution.started_at >= last_24h
            ).count()
            
            successful_calls_24h = db.query(ToolExecution).filter(
                ToolExecution.integration_id.in_([i.id for i in integrations]),
                ToolExecution.started_at >= last_24h,
                ToolExecution.success == True
            ).count()
            
            initial_data = {
                "type": "initial_data",
                "data": {
                    "summary": {
                        "total_integrations": len(integrations),
                        "active_integrations": len([i for i in integrations if i.status == IntegrationStatus.ACTIVE]),
                        "total_calls_24h": total_calls_24h,
                        "successful_calls_24h": successful_calls_24h,
                        "success_rate_24h": (successful_calls_24h / total_calls_24h * 100) if total_calls_24h > 0 else 0
                    },
                    "integrations": [
                        {
                            "id": integration.id,
                            "name": integration.name,
                            "type": integration.integration_type.value,
                            "status": integration.status.value,
                            "health_status": integration.health_status or "unknown"
                        }
                        for integration in integrations
                    ]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.send_to_connection(connection_id, initial_data)
            
        except Exception as e:
            logger.error(f"Failed to send initial analytics data: {e}")
        finally:
            db.close()
    
    async def _analytics_streaming_task(self):
        """Background task for streaming analytics updates."""
        self.analytics_task_running = True
        logger.info("Starting analytics streaming task")
        
        try:
            while self.active_connections:
                await self._collect_and_broadcast_analytics()
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except asyncio.CancelledError:
            logger.info("Analytics streaming task cancelled")
        except Exception as e:
            logger.error(f"Analytics streaming task error: {e}")
        finally:
            self.analytics_task_running = False
    
    async def _collect_and_broadcast_analytics(self):
        """Collect current analytics data and broadcast to all connections."""
        try:
            db = next(get_db_session())
            
            # Get system-wide metrics
            current_time = datetime.utcnow()
            last_minute = current_time - timedelta(minutes=1)
            last_hour = current_time - timedelta(hours=1)
            
            # Recent activity
            recent_executions = db.query(ToolExecution).filter(
                ToolExecution.started_at >= last_minute
            ).order_by(desc(ToolExecution.started_at)).limit(10).all()
            
            if recent_executions:
                activity_data = {
                    "type": AnalyticsEvent.TOOL_EXECUTION,
                    "data": {
                        "recent_executions": [
                            {
                                "id": execution.id,
                                "tool_name": execution.tool_name,
                                "integration_id": execution.integration_id,
                                "success": execution.success,
                                "execution_time": execution.execution_time,
                                "started_at": execution.started_at.isoformat()
                            }
                            for execution in recent_executions
                        ],
                        "count": len(recent_executions)
                    },
                    "timestamp": current_time.isoformat()
                }
                
                await self.broadcast_to_all(activity_data, AnalyticsEvent.TOOL_EXECUTION)
            
            # Performance metrics (every 30 seconds)
            if int(current_time.timestamp()) % 30 == 0:
                hourly_metrics = db.query(
                    func.count(ToolExecution.id).label('total_calls'),
                    func.sum(func.case([(ToolExecution.success == True, 1)], else_=0)).label('successful_calls'),
                    func.avg(ToolExecution.execution_time).label('avg_response_time')
                ).filter(
                    ToolExecution.started_at >= last_hour
                ).first()
                
                performance_data = {
                    "type": AnalyticsEvent.PERFORMANCE_DATA,
                    "data": {
                        "period": "last_hour",
                        "total_calls": hourly_metrics.total_calls or 0,
                        "successful_calls": hourly_metrics.successful_calls or 0,
                        "success_rate": (hourly_metrics.successful_calls / hourly_metrics.total_calls * 100) if hourly_metrics.total_calls else 0,
                        "avg_response_time_ms": round(hourly_metrics.avg_response_time * 1000, 2) if hourly_metrics.avg_response_time else 0
                    },
                    "timestamp": current_time.isoformat()
                }
                
                await self.broadcast_to_all(performance_data, AnalyticsEvent.PERFORMANCE_DATA)
            
            # Integration health checks (every 60 seconds)
            if int(current_time.timestamp()) % 60 == 0:
                integrations = db.query(Integration).all()
                
                health_data = {
                    "type": AnalyticsEvent.SYSTEM_HEALTH,
                    "data": {
                        "integrations": [
                            {
                                "id": integration.id,
                                "name": integration.name,
                                "type": integration.integration_type.value,
                                "status": integration.status.value,
                                "health_status": integration.health_status or "unknown",
                                "last_health_check": integration.last_health_check.isoformat() if integration.last_health_check else None,
                                "error_count": integration.error_count or 0
                            }
                            for integration in integrations
                        ],
                        "summary": {
                            "total": len(integrations),
                            "healthy": len([i for i in integrations if i.health_status == "healthy"]),
                            "unhealthy": len([i for i in integrations if i.health_status == "unhealthy"]),
                            "unknown": len([i for i in integrations if not i.health_status or i.health_status == "unknown"])
                        }
                    },
                    "timestamp": current_time.isoformat()
                }
                
                await self.broadcast_to_all(health_data, AnalyticsEvent.SYSTEM_HEALTH)
            
        except Exception as e:
            logger.error(f"Failed to collect and broadcast analytics: {e}")
        finally:
            db.close()
    
    async def send_custom_analytics_event(self, event_type: str, data: Dict[str, Any], user_id: str = None):
        """Send custom analytics event to specific user or broadcast to all."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast_to_all(message, event_type)


# Global instance
analytics_websocket_manager = AnalyticsWebSocketManager()