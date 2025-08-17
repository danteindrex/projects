from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class ChatMessageBase(BaseModel):
    content: str
    message_type: str  # user, assistant, system, tool_call, thinking
    role: str  # user, assistant, system
    metadata: Optional[Dict[str, Any]] = {}

class ChatMessageCreate(ChatMessageBase):
    session_id: int
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    tool_status: Optional[str] = None

class ChatMessageResponse(ChatMessageBase):
    id: int
    external_id: str
    session_id: int
    tokens_used: int
    processing_time: int
    tool_name: Optional[str]
    tool_input: Optional[str]
    tool_output: Optional[str]
    tool_status: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class ChatSessionResponse(BaseModel):
    id: int
    external_id: str
    title: Optional[str]
    status: str
    total_messages: int
    last_activity: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str  # token, agent_event, tool_result, notice, final
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    session_id: int
    message_id: int
    content: str
    message_type: str
    metadata: Optional[Dict[str, Any]] = {}

class ToolCallEvent(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    status: str  # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None

class AgentEvent(BaseModel):
    event_type: str  # thinking, planning, tool_call, waiting, complete
    agent_id: Optional[str] = None
    details: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
