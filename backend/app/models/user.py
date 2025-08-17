from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    INTEGRATOR = "integrator"

class User(BaseModel):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_verified = Column(Boolean, default=False)
    last_login = Column(String(255))
    
    # Relationships
    integrations = relationship("Integration", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
