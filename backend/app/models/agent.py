from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import enum
from .base import TenantModel

class AgentType(str, enum.Enum):
    INTEGRATION = "integration"
    ROUTER = "router"
    SPECIALIST = "specialist"

class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"

class Agent(TenantModel):
    """Agent model for CrewAI agents"""
    __tablename__ = "agents"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.INACTIVE)
    
    # Agent configuration
    config = Column(JSON, default={})
    capabilities = Column(JSON, default=[])
    tools = Column(JSON, default=[])
    
    # Performance metrics
    total_requests = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # percentage
    avg_response_time = Column(Integer, default=0)  # milliseconds
    last_used = Column(String(255))
    
    # Relationships
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=True)
    integration = relationship("Integration", back_populates="agents")
    
    def __repr__(self):
        return f"<Agent {self.name} ({self.agent_type})>"
