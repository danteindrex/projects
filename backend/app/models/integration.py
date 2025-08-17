from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from .base import TenantModel
import enum

class IntegrationType(str, enum.Enum):
    JIRA = "jira"
    ZENDESK = "zendesk"
    SALESFORCE = "salesforce"
    GITHUB = "github"
    CUSTOM = "custom"

class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"

class Integration(TenantModel):
    """Integration model for connected business systems"""
    __tablename__ = "integrations"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    base_url = Column(String(500), nullable=False)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.TESTING)
    
    # Encrypted credentials
    encrypted_credentials = Column(Text, nullable=False)
    encryption_key_id = Column(String(255), nullable=False)
    
    # Configuration
    config = Column(JSON, default={})
    rate_limit = Column(Integer, default=100)  # requests per minute
    timeout = Column(Integer, default=30)  # seconds
    
    # Health monitoring
    last_health_check = Column(String(255))
    health_status = Column(String(50), default="unknown")
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="integrations")
    agents = relationship("Agent", back_populates="integration")
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.integration_type})>"
