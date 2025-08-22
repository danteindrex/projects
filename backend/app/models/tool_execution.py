"""
Database models for tool execution tracking.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.database import Base


class ToolExecution(Base):
    """Track tool execution events and results."""
    __tablename__ = "tool_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Execution metadata
    tool_name = Column(String(100), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Execution details
    parameters = Column(JSON, default={})
    success = Column(Boolean, nullable=False, default=False)
    result_data = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, default=0.0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    integration = relationship("Integration")
    user = relationship("User")
    events = relationship("ToolExecutionEvent", back_populates="execution", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_tool_execution_session", "session_id", "started_at"),
        Index("idx_tool_execution_user_time", "user_id", "started_at"),
        Index("idx_tool_execution_integration_time", "integration_id", "started_at"),
        Index("idx_tool_execution_tool_time", "tool_name", "started_at"),
    )
    
    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool={self.tool_name}, success={self.success})>"


class ToolExecutionEvent(Base):
    """Track individual events during tool execution."""
    __tablename__ = "tool_execution_events"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("tool_executions.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # start, progress, complete, error
    message = Column(Text, nullable=False)
    event_data = Column(JSON, default={})
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    execution = relationship("ToolExecution", back_populates="events")
    
    def __repr__(self):
        return f"<ToolExecutionEvent(id={self.id}, type={self.event_type}, execution_id={self.execution_id})>"


class StreamingEvent(Base):
    """Track streaming events sent to clients."""
    __tablename__ = "streaming_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event metadata
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # token, agent_event, tool_call, thinking, final, error
    
    # Event content
    content = Column(Text, nullable=False)
    event_metadata = Column(JSON, default={})
    
    # Optional tool reference
    tool_name = Column(String(100), nullable=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=True, index=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    integration = relationship("Integration")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_streaming_session_time", "session_id", "timestamp"),
        Index("idx_streaming_user_time", "user_id", "timestamp"),
        Index("idx_streaming_type_time", "event_type", "timestamp"),
    )
    
    def __repr__(self):
        return f"<StreamingEvent(id={self.id}, type={self.event_type}, session={self.session_id})>"


class AgentActivity(Base):
    """Track agent activities and performance."""
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Agent metadata
    agent_id = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # router, integration
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=True, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # created, query_processed, task_executed, etc.
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Performance metrics
    processing_time = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    tools_called = Column(Integer, default=0)
    
    # Activity data
    input_data = Column(JSON, default={})
    result_data = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    integration = relationship("Integration")
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_agent_activity_agent_time", "agent_id", "timestamp"),
        Index("idx_agent_activity_user_time", "user_id", "timestamp"),
        Index("idx_agent_activity_session_time", "session_id", "timestamp"),
        Index("idx_agent_activity_type_time", "activity_type", "timestamp"),
    )
    
    def __repr__(self):
        return f"<AgentActivity(id={self.id}, agent={self.agent_id}, activity={self.activity_type})>"