from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum, Integer, Index, DateTime
from sqlalchemy.orm import relationship
from .base import TenantModel, Base
from datetime import datetime
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

class AuthType(str, enum.Enum):
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    KEY_TOKEN = "key_token"

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
    
    # Authentication
    auth_type = Column(Enum(AuthType), default=AuthType.API_KEY)
    oauth_scopes = Column(JSON, default=[])  # Requested OAuth scopes
    token_expires_at = Column(DateTime)  # When access token expires
    
    # Health monitoring
    last_health_check = Column(String(255))
    health_status = Column(String(50), default="unknown")
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="integrations")
    oauth_states = relationship("OAuthState", back_populates="integration")
    
    # Define indexes for better query performance
    __table_args__ = (
        Index('idx_integration_owner_status', 'owner_id', 'status'),
        Index('idx_integration_tenant_type', 'tenant_id', 'integration_type'),
        Index('idx_integration_type_health', 'integration_type', 'health_status'),
        Index('idx_integration_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.integration_type})>"

class OAuthState(Base):
    """OAuth state tracking for CSRF protection"""
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), nullable=False, unique=True, index=True)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=True)  # Set after creation
    
    # OAuth flow data
    client_id = Column(String(255), nullable=False)
    scopes = Column(JSON, default=[])
    redirect_uri = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # States should expire
    used_at = Column(DateTime, nullable=True)  # When the state was consumed
    
    # Status
    is_used = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    integration = relationship("Integration", back_populates="oauth_states")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_oauth_state_user_type', 'user_id', 'integration_type'),
        Index('idx_oauth_state_expires', 'expires_at'),
        Index('idx_oauth_state_used', 'is_used', 'created_at'),
    )
    
    def __repr__(self):
        return f"<OAuthState {self.state[:8]}... ({self.integration_type})>"
