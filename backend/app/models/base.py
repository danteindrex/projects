from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class TenantModel(BaseModel):
    """Base model for multi-tenant entities"""
    __abstract__ = True
    
    tenant_id = Column(String(36), nullable=False, index=True)
    external_id = Column(String(255), unique=True, index=True)
    
    def __init__(self, **kwargs):
        if 'external_id' not in kwargs:
            kwargs['external_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
