from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, Dict, Any, List
from app.models.integration import IntegrationType, IntegrationStatus

class IntegrationBase(BaseModel):
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    base_url: HttpUrl
    config: Optional[Dict[str, Any]] = {}
    rate_limit: Optional[int] = 100
    timeout: Optional[int] = 30

class IntegrationCreate(IntegrationBase):
    credentials: Dict[str, str]  # Will be encrypted before storage
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('Integration name must be at least 2 characters long')
        return v
    
    @validator('base_url')
    def validate_url(cls, v):
        if not str(v).startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None
    status: Optional[IntegrationStatus] = None

class IntegrationResponse(IntegrationBase):
    id: int
    external_id: str
    tenant_id: str
    status: IntegrationStatus
    health_status: str
    error_count: int
    last_error: Optional[str]
    last_health_check: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class IntegrationTestRequest(BaseModel):
    base_url: HttpUrl
    credentials: Dict[str, str]
    test_endpoint: Optional[str] = "/health"
    timeout: Optional[int] = 30

class IntegrationTestResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_details: Optional[str] = None

class IntegrationHealth(BaseModel):
    integration_id: int
    status: str
    response_time: float
    last_check: str
    error_count: int
    uptime_percentage: float
