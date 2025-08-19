"""
Common dependencies for API endpoints
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db_session
from app.models.user import User
from app.core.security import get_current_active_user

def get_db():
    """Get database session dependency"""
    db = next(get_db_session())
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    return get_current_active_user(db)

def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account not verified"
        )
    return current_user