"""OAuth endpoints for integration authentication"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

from app.api import deps
from app.core.logging import log_event
from app.db.database import get_db
from app.models.integration import IntegrationType
from app.services.oauth_service import oauth_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class OAuthAuthorizationRequest(BaseModel):
    integration_type: IntegrationType
    client_id: str
    scopes: Optional[List[str]] = None
    custom_config: Optional[Dict[str, Any]] = None

class OAuthAuthorizationResponse(BaseModel):
    authorization_url: str
    state: str
    integration_type: str

class OAuthCallbackRequest(BaseModel):
    integration_type: IntegrationType
    authorization_code: str
    state: str
    client_id: str
    client_secret: str
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class OAuthTokenRefreshRequest(BaseModel):
    integration_id: int
    refresh_token: str

class OAuthSupportResponse(BaseModel):
    integration_type: str
    supports_oauth: bool
    oauth_config: Optional[Dict[str, Any]] = None

@router.get("/oauth/support/{integration_type}", response_model=OAuthSupportResponse)
async def get_oauth_support(
    integration_type: IntegrationType,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get OAuth support information for integration type"""
    try:
        supports_oauth = oauth_service.supports_oauth(integration_type)
        oauth_config = None
        
        if supports_oauth:
            oauth_config = oauth_service.get_oauth_config(integration_type)
            # Remove sensitive information
            if oauth_config:
                oauth_config = {
                    "scopes": oauth_config.get("scopes", []),
                    "default_scopes": oauth_config.get("default_scopes", []),
                    "redirect_uri_required": oauth_config.get("redirect_uri_required", True),
                    "note": oauth_config.get("note", "")
                }
        
        return OAuthSupportResponse(
            integration_type=integration_type.value,
            supports_oauth=supports_oauth,
            oauth_config=oauth_config
        )
    except Exception as e:
        logger.error(f"Error getting OAuth support info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OAuth support information")

@router.post("/oauth/authorize", response_model=OAuthAuthorizationResponse)
async def initiate_oauth_flow(
    request: OAuthAuthorizationRequest,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Initiate OAuth authorization flow"""
    try:
        if not oauth_service.supports_oauth(request.integration_type):
            raise HTTPException(
                status_code=400, 
                detail=f"OAuth not supported for {request.integration_type}"
            )
        
        authorization_url, state = oauth_service.generate_authorization_url(
            integration_type=request.integration_type,
            client_id=request.client_id,
            scopes=request.scopes
        )
        
        # Log OAuth initiation
        log_event(
            "oauth_flow_initiated",
            integration_type=request.integration_type.value,
            user_id=current_user.id,
            scopes=request.scopes or []
        )
        
        return OAuthAuthorizationResponse(
            authorization_url=authorization_url,
            state=state,
            integration_type=request.integration_type.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

@router.post("/oauth/callback")
async def handle_oauth_callback(
    request: OAuthCallbackRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
):
    """Handle OAuth callback and create integration"""
    try:
        if not oauth_service.supports_oauth(request.integration_type):
            raise HTTPException(
                status_code=400, 
                detail=f"OAuth not supported for {request.integration_type}"
            )
        
        # Create integration using OAuth
        integration = await oauth_service.create_oauth_integration(
            db=db,
            name=request.name,
            integration_type=request.integration_type,
            client_id=request.client_id,
            client_secret=request.client_secret,
            authorization_code=request.authorization_code,
            state=request.state,
            user_id=current_user.id,
            config=request.config
        )
        
        return {
            "id": integration.id,
            "name": integration.name,
            "integration_type": integration.integration_type.value,
            "status": integration.status.value,
            "health_status": integration.health_status,
            "created_at": integration.created_at.isoformat() if integration.created_at else None,
            "message": "OAuth integration created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback handling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth flow: {str(e)}")

@router.post("/oauth/refresh/{integration_id}")
async def refresh_oauth_token(
    integration_id: int,
    request: OAuthTokenRefreshRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
):
    """Refresh OAuth access token"""
    try:
        # Get integration
        from app.models.integration import Integration
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Refresh token
        token_data = await oauth_service.refresh_access_token(
            integration=integration,
            refresh_token=request.refresh_token
        )
        
        # Update integration credentials
        from app.services.integration_service import integration_service
        from app.core.encryption import decrypt_credentials, encrypt_credentials
        
        credentials = decrypt_credentials(integration.encrypted_credentials)
        credentials["access_token"] = token_data["access_token"]
        
        if "refresh_token" in token_data:
            credentials["refresh_token"] = token_data["refresh_token"]
        
        if "expires_in" in token_data:
            credentials["expires_in"] = str(token_data["expires_in"])
        
        credentials["refreshed_at"] = token_data["refreshed_at"]
        
        # Update in database
        integration.encrypted_credentials = encrypt_credentials(credentials)
        db.commit()
        
        log_event(
            "oauth_token_refreshed",
            integration_id=integration.id,
            user_id=current_user.id
        )
        
        return {
            "message": "Token refreshed successfully",
            "expires_in": token_data.get("expires_in"),
            "refreshed_at": token_data["refreshed_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

@router.delete("/oauth/revoke/{integration_id}")
async def revoke_oauth_token(
    integration_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke OAuth access token"""
    try:
        # Get integration
        from app.models.integration import Integration
        from app.core.encryption import decrypt_credentials
        
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Get access token
        credentials = decrypt_credentials(integration.encrypted_credentials)
        access_token = credentials.get("access_token")
        
        if access_token:
            # Attempt to revoke token
            revoked = await oauth_service.revoke_token(integration, access_token)
            
            if revoked:
                log_event(
                    "oauth_token_revoked",
                    integration_id=integration.id,
                    user_id=current_user.id
                )
        
        return {"message": "Token revocation completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke token")

# Additional endpoint for getting available scopes for an integration type
@router.get("/oauth/scopes/{integration_type}")
async def get_available_scopes(
    integration_type: IntegrationType,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get available OAuth scopes for integration type"""
    try:
        if not oauth_service.supports_oauth(integration_type):
            raise HTTPException(
                status_code=400, 
                detail=f"OAuth not supported for {integration_type}"
            )
        
        oauth_config = oauth_service.get_oauth_config(integration_type)
        
        return {
            "integration_type": integration_type.value,
            "available_scopes": oauth_config.get("scopes", []),
            "default_scopes": oauth_config.get("default_scopes", []),
            "user_scopes": oauth_config.get("user_scopes", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OAuth scopes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OAuth scopes")