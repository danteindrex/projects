from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum, Integer, Index
from sqlalchemy.orm import relationship
from .base import TenantModel
import enum

class IntegrationType(str, enum.Enum):
    # Project Management
    JIRA = "jira"
    ASANA = "asana"
    TRELLO = "trello"
    MONDAY = "monday"
    CLICKUP = "clickup"
    
    # Customer Support
    ZENDESK = "zendesk"
    FRESHDESK = "freshdesk"
    INTERCOM = "intercom"
    SERVICENOW = "servicenow"
    
    # CRM Systems
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO_CRM = "zoho_crm"
    
    # Development Tools
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    
    # Communication
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft_teams"
    DISCORD = "discord"
    
    # ERP Systems
    NETSUITE = "netsuite"
    SAP = "sap"
    DYNAMICS365 = "dynamics365"
    ODOO = "odoo"
    
    # Marketing
    MAILCHIMP = "mailchimp"
    HUBSPOT_MARKETING = "hubspot_marketing"
    MARKETO = "marketo"
    
    # Analytics
    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"
    
    # Cloud Platforms
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    
    # Custom API
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
    
    # Define indexes for better query performance
    __table_args__ = (
        Index('idx_integration_owner_status', 'owner_id', 'status'),
        Index('idx_integration_tenant_type', 'tenant_id', 'integration_type'),
        Index('idx_integration_type_health', 'integration_type', 'health_status'),
        Index('idx_integration_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.integration_type})>"
