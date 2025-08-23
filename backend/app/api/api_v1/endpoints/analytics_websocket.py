"""
Real-time analytics WebSocket endpoint for live dashboard updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List
import asyncio
import json
from datetime import datetime

from app.core.security import get_current_active_user_ws
from app.models.user import User
from app.services.analytics_websocket_service import analytics_websocket_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

class AnalyticsConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"Analytics WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"Analytics WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove broken connections
                    self.active_connections[user_id].remove(connection)
    
    async def broadcast_to_user(self, message: dict, user_id: int):
        await self.send_personal_message(message, user_id)

analytics_manager = AnalyticsConnectionManager()

@router.websocket("/analytics/ws")
async def analytics_websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """WebSocket endpoint for real-time analytics updates."""
    
    # Authenticate user
    try:
        user = await get_current_active_user_ws(token)
        if not user:
            await websocket.close(code=1008, reason="Authentication required")
            return
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    await analytics_manager.connect(websocket, user.id)
    
    try:
        # Send initial analytics data
        await send_initial_analytics(websocket, user.id)
        
        # Start periodic updates
        update_task = asyncio.create_task(
            periodic_analytics_updates(websocket, user.id)
        )
        
        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "request_update":
                    await send_analytics_update(websocket, user.id)
                elif message.get("type") == "subscribe_integration":
                    integration_id = message.get("integration_id")
                    await subscribe_to_integration(websocket, user.id, integration_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Analytics WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        analytics_manager.disconnect(websocket, user.id)
        if 'update_task' in locals():
            update_task.cancel()

async def send_initial_analytics(websocket: WebSocket, user_id: int):
    """Send initial analytics data when client connects."""
    try:
        # Get initial analytics data
        analytics_data = await analytics_websocket_service.get_user_analytics_summary(user_id)
        
        await websocket.send_text(json.dumps({
            "type": "initial_analytics",
            "data": analytics_data,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Failed to send initial analytics: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to load initial analytics"
        }))

async def send_analytics_update(websocket: WebSocket, user_id: int):
    """Send analytics update to client."""
    try:
        # Get updated analytics data
        analytics_data = await analytics_websocket_service.get_user_analytics_summary(user_id)
        
        await websocket.send_text(json.dumps({
            "type": "analytics_update",
            "data": analytics_data,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Failed to send analytics update: {e}")

async def subscribe_to_integration(websocket: WebSocket, user_id: int, integration_id: int):
    """Subscribe to updates for a specific integration."""
    try:
        # Get integration-specific analytics
        integration_data = await analytics_websocket_service.get_integration_analytics(
            user_id, integration_id
        )
        
        await websocket.send_text(json.dumps({
            "type": "integration_analytics",
            "integration_id": integration_id,
            "data": integration_data,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Failed to get integration analytics: {e}")

async def periodic_analytics_updates(websocket: WebSocket, user_id: int):
    """Send periodic analytics updates every 30 seconds."""
    try:
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            await send_analytics_update(websocket, user_id)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Periodic analytics update error: {e}")

# Function to broadcast analytics updates to all connected users
async def broadcast_analytics_update(user_id: int, update_data: dict):
    """Broadcast analytics update to specific user's connections."""
    message = {
        "type": "live_update",
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await analytics_manager.broadcast_to_user(message, user_id)

# Export the manager for use in other services
__all__ = ["analytics_manager", "broadcast_analytics_update"]