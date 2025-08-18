from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import TenantModel

class ChatSession(TenantModel):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    title = Column(String(255))
    status = Column(String(50), default="active")  # active, closed, archived
    
    # Session metadata
    session_metadata = Column(JSON, default={})
    total_messages = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Define indexes for better query performance
    __table_args__ = (
        Index('idx_chat_session_user_status', 'user_id', 'status'),
        Index('idx_chat_session_tenant_activity', 'tenant_id', 'last_activity'),
        Index('idx_chat_session_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatSession {self.id} ({self.status})>"

class ChatMessage(TenantModel):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False)  # user, assistant, system, tool_call, thinking
    role = Column(String(50), nullable=False)  # user, assistant, system
    
    # Message metadata
    message_metadata = Column(JSON, default={})
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Integer, default=0)  # milliseconds
    
    # Tool calling info
    tool_name = Column(String(255))
    tool_input = Column(Text)
    tool_output = Column(Text)
    tool_status = Column(String(50))  # pending, running, completed, failed
    
    # Relationships
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    session = relationship("ChatSession", back_populates="messages")
    
    # Define indexes for better query performance
    __table_args__ = (
        Index('idx_chat_message_session_created', 'session_id', 'created_at'),
        Index('idx_chat_message_tenant_session', 'tenant_id', 'session_id'),
        Index('idx_chat_message_type_role', 'message_type', 'role'),
        Index('idx_chat_message_tool_status', 'tool_status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage {self.id} ({self.message_type})>"
