from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.security import get_current_active_user
from app.db.database import get_db_session
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse, WebSocketMessage, ToolCallEvent, AgentEvent
from app.core.logging import log_websocket_event, log_event
from app.core.kafka_service import publish_chat_event
from app.services.streaming_service import streaming_service, websocket_manager

router = APIRouter()





@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time chat with token authentication"""
    connection_id = None
    user_id = None
    try:
        # Authenticate token
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
            
        # Verify token 
        try:
            from app.core.security import verify_token
            payload = verify_token(token)
            if not payload:
                await websocket.close(code=1008, reason="Invalid token")
                return
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token payload")
                return
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            await websocket.close(code=1008, reason="Token validation failed")
            return
        
        # Accept the connection after authentication
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        # Create a default session if needed
        session_id = f"session_{user_id}_{connection_id[:8]}"
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established", 
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        log_websocket_event(connection_id, "websocket_connected", session_id=session_id, user_id=user_id)
        
        # Register connection with streaming service
        stream_connection_id = await websocket_manager.connect(websocket, session_id)
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process message directly with proper streaming
                user_message = message_data.get("message", "")
                if user_message:
                    logger.info(f"Processing: {user_message[:50]}...")
                    
                    # Get database session
                    from app.db.database import get_db_session
                    db = next(get_db_session())
                    
                    try:
                        # Stream AI responses with proper buffer flushing
                        async for stream_event in streaming_service.process_query_streaming(
                            user_message, user_id, session_id, db
                        ):
                            await websocket.send_text(json.dumps(stream_event))
                            await asyncio.sleep(0)  # Critical: flush WebSocket buffer
                            
                            if stream_event.get("type") == "final":
                                break
                    except Exception as e:
                        logger.error(f"Streaming failed: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error", 
                            "content": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                    finally:
                        db.close()
                
            except WebSocketDisconnect:
                log_websocket_event(connection_id, "websocket_disconnected")
                websocket_manager.disconnect(stream_connection_id, session_id)
                break
            except Exception as e:
                log_websocket_event(connection_id, "websocket_error", error=str(e))
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "An error occurred processing your message",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                websocket_manager.disconnect(stream_connection_id, session_id)
                
    except Exception as e:
        log_websocket_event(connection_id or "unknown", "websocket_connection_error", error=str(e))
    





# REST endpoints for chat management
@router.post("/sessions", response_model=ChatResponse)
async def create_chat_session(
    session_data: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Create a new chat session"""
    try:
        # Create new session
        db_session = ChatSession(
            title=session_data.message[:50] + "..." if len(session_data.message) > 50 else session_data.message,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id if hasattr(current_user, 'tenant_id') else "default"
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Publish chat session created event
        try:
            await publish_chat_event(str(db_session.id), "session_created", {
                "user_id": current_user.id,
                "title": db_session.title,
                "tenant_id": db_session.tenant_id
            })
        except Exception as e:
            logger.warning(f"Failed to publish chat session event: {e}")
        
        # Create first message
        db_message = ChatMessage(
            content=session_data.message,
            message_type="user",
            role="user",
            session_id=db_session.id,
            tenant_id=db_session.tenant_id
        )
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Publish chat message event
        try:
            await publish_chat_event(str(db_session.id), "message_created", {
                "message_id": db_message.id,
                "user_id": current_user.id,
                "message_type": db_message.message_type,
                "role": db_message.role
            })
        except Exception as e:
            logger.warning(f"Failed to publish chat message event: {e}")
        
        log_event("chat_session_created", session_id=db_session.id, user_id=current_user.id)
        
        return ChatResponse(
            session_id=db_session.id,
            message_id=db_message.id,
            content=db_message.content,
            message_type=db_message.message_type,
            metadata={"session_title": db_session.title}
        )
        
    except Exception as e:
        db.rollback()
        log_event("chat_session_creation_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/sessions", response_model=List[ChatResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get user's chat sessions"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.last_activity.desc()).limit(20).all()
        
        return [
            ChatResponse(
                session_id=session.id,
                message_id=0,  # Placeholder
                content=session.title or "Untitled session",
                message_type="session",
                metadata={"status": session.status, "total_messages": session.total_messages}
            )
            for session in sessions
        ]
        
    except Exception as e:
        log_event("chat_sessions_retrieval_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatResponse])
async def get_chat_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get messages for a specific chat session"""
    try:
        # Verify session ownership
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Get messages for the session
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [
            ChatResponse(
                session_id=session_id,
                message_id=message.id,
                content=message.content,
                message_type=message.message_type,
                metadata={
                    "role": message.role,
                    "tokens_used": message.tokens_used,
                    "processing_time": message.processing_time,
                    "tool_name": message.tool_name,
                    "tool_status": message.tool_status,
                    "timestamp": message.created_at.isoformat()
                }
            )
            for message in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        log_event("chat_messages_retrieval_failed", error=str(e), user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat messages"
        )

@router.get("/sessions/current", response_model=ChatResponse)
async def get_or_create_current_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get or create the current active chat session for the user"""
    try:
        # Look for an active session
        session = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id,
            ChatSession.status == "active"
        ).order_by(ChatSession.last_activity.desc()).first()
        
        # If no active session, create one
        if not session:
            session = ChatSession(
                title="New Chat",
                user_id=current_user.id,
                tenant_id=current_user.tenant_id if hasattr(current_user, 'tenant_id') else "default",
                status="active"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Publish session created event
            try:
                await publish_chat_event(str(session.id), "session_created", {
                    "user_id": current_user.id,
                    "title": session.title,
                    "tenant_id": session.tenant_id
                })
            except Exception as e:
                logger.warning(f"Failed to publish chat session event: {e}")
        
        return ChatResponse(
            session_id=session.id,
            message_id=0,
            content=session.title or "Current session",
            message_type="session",
            metadata={
                "status": session.status,
                "total_messages": session.total_messages,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat() if session.last_activity else None
            }
        )
        
    except Exception as e:
        db.rollback()
        log_event("current_session_retrieval_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get or create current session"
        )
