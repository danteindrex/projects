"""OAuth Service for handling OAuth 2.0 authentication flows"""

import asyncio
import aiohttp
import secrets
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import base64

from app.models.integration import Integration, IntegrationType
from app.services.integration_service import IntegrationTemplates
from app.core.encryption import encrypt_credentials, decrypt_credentials
from app.core.logging import log_event
from app.core.config import settings

logger = logging.getLogger(__name__)

class OAuthService:
    """Service for managing OAuth 2.0 authentication flows"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        self.redirect_base_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        
    def get_oauth_config(self, integration_type: IntegrationType) -> Dict[str, Any]:
        """Get OAuth configuration for integration type"""
        template = IntegrationTemplates.TEMPLATES.get(integration_type, {})
        return template.get("oauth_config", {})
    
    def supports_oauth(self, integration_type: IntegrationType) -> bool:
        """Check if integration type supports OAuth"""
        oauth_config = self.get_oauth_config(integration_type)
        return oauth_config.get("supports_oauth", False)
    
    def generate_authorization_url(
        self, 
        integration_type: IntegrationType,
        client_id: str,
        scopes: Optional[list] = None,
        state: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate OAuth authorization URL and state parameter"""
        
        oauth_config = self.get_oauth_config(integration_type)
        if not oauth_config.get("supports_oauth"):
            raise ValueError(f"OAuth not supported for {integration_type}")
        
        # Generate state for CSRF protection
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Use provided scopes or default scopes
        if not scopes:
            scopes = oauth_config.get("default_scopes", [])
        
        # Build redirect URI
        redirect_uri = f"{self.redirect_base_url}/integrations/oauth/callback"
        
        # Build authorization URL
        auth_url = oauth_config["authorization_url"]
        
        # Handle template URLs (like Zendesk with {subdomain})
        if "{" in auth_url:
            # For now, we'll need to handle these case by case
            # This would need additional parameters passed in
            pass
        
        # Build parameters
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
        }
        
        # Add scopes if provided
        if scopes:
            if integration_type == IntegrationType.SLACK:
                # Slack uses separate scope and user_scope parameters
                params["scope"] = " ".join(scopes)
                user_scopes = oauth_config.get("user_scopes", [])
                if user_scopes:
                    params["user_scope"] = " ".join(user_scopes)
            else:
                params["scope"] = " ".join(scopes)
        
        # Add any integration-specific parameters
        if integration_type == IntegrationType.SALESFORCE:
            # Salesforce requires prompt parameter for better UX
            params["prompt"] = "consent"
        
        authorization_url = f"{auth_url}?{urlencode(params)}"
        return authorization_url, state
    
    async def exchange_code_for_token(
        self,
        integration_type: IntegrationType,
        authorization_code: str,
        client_id: str,
        client_secret: str,
        state: str,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        
        oauth_config = self.get_oauth_config(integration_type)
        if not oauth_config.get("supports_oauth"):
            raise ValueError(f"OAuth not supported for {integration_type}")
        
        token_url = oauth_config["token_url"]
        
        if not redirect_uri:
            redirect_uri = f"{self.redirect_base_url}/integrations/oauth/callback"
        
        # Prepare token exchange parameters
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        # Some APIs require different authentication methods
        if integration_type == IntegrationType.GITHUB:
            headers["Accept"] = "application/json"  # GitHub requires this
        elif integration_type == IntegrationType.HUBSPOT:
            # HubSpot uses form data
            pass
        elif integration_type == IntegrationType.SLACK:
            # Slack uses form data but with specific headers
            pass
        
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.post(token_url, data=data, headers=headers) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        
                        # Validate required fields
                        if "access_token" not in token_data:
                            raise ValueError("No access token in response")
                        
                        # Add metadata
                        token_data["obtained_at"] = datetime.utcnow().isoformat()
                        token_data["integration_type"] = integration_type.value
                        
                        return token_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Token exchange failed: {response.status} - {error_text}")
                        raise Exception(f"Token exchange failed: {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception("Token exchange timeout")
        except Exception as e:
            logger.error(f"OAuth token exchange failed for {integration_type}: {e}")
            raise
    
    async def refresh_access_token(
        self,
        integration: Integration,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh an expired access token"""
        
        integration_type = integration.integration_type
        oauth_config = self.get_oauth_config(integration_type)
        
        if not oauth_config.get("supports_oauth"):
            raise ValueError(f"OAuth not supported for {integration_type}")
        
        # Decrypt credentials to get client_id and client_secret
        credentials = decrypt_credentials(integration.encrypted_credentials)
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        
        if not client_id or not client_secret:
            raise ValueError("Missing OAuth client credentials")
        
        token_url = oauth_config["token_url"]
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.post(token_url, data=data, headers=headers) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        
                        # Add metadata
                        token_data["refreshed_at"] = datetime.utcnow().isoformat()
                        token_data["integration_type"] = integration_type.value
                        
                        return token_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: {response.status} - {error_text}")
                        raise Exception(f"Token refresh failed: {error_text}")
                        
        except Exception as e:
            logger.error(f"Token refresh failed for integration {integration.id}: {e}")
            raise
    
    async def revoke_token(
        self,
        integration: Integration,
        access_token: str
    ) -> bool:
        """Revoke an access token"""
        
        integration_type = integration.integration_type
        oauth_config = self.get_oauth_config(integration_type)
        
        # Not all APIs support token revocation
        revoke_url = oauth_config.get("revoke_url")
        if not revoke_url:
            logger.warning(f"Token revocation not supported for {integration_type}")
            return True  # Consider it successful if not supported
        
        try:
            credentials = decrypt_credentials(integration.encrypted_credentials)
            client_id = credentials.get("client_id")
            
            data = {
                "token": access_token,
                "client_id": client_id,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.post(revoke_url, data=data, headers=headers) as response:
                    return response.status in [200, 204]
                    
        except Exception as e:
            logger.error(f"Token revocation failed for integration {integration.id}: {e}")
            return False
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if access token is expired"""
        
        if "expires_in" not in token_data or "obtained_at" not in token_data:
            return False  # Can't determine expiry
        
        try:
            obtained_at = datetime.fromisoformat(token_data["obtained_at"])
            expires_in = token_data["expires_in"]  # seconds
            expiry_time = obtained_at + timedelta(seconds=expires_in)
            
            # Add 5 minute buffer
            return datetime.utcnow() >= (expiry_time - timedelta(minutes=5))
        except (ValueError, KeyError):
            return False
    
    def build_oauth_credentials(
        self, 
        client_id: str, 
        client_secret: str, 
        token_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Build credentials dictionary for OAuth integration"""
        
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_data["access_token"],
        }
        
        # Add refresh token if available
        if "refresh_token" in token_data:
            credentials["refresh_token"] = token_data["refresh_token"]
        
        # Add token metadata
        if "expires_in" in token_data:
            credentials["expires_in"] = str(token_data["expires_in"])
        
        if "obtained_at" in token_data:
            credentials["obtained_at"] = token_data["obtained_at"]
        
        # Add integration-specific fields
        if "scope" in token_data:
            credentials["scope"] = token_data["scope"]
        
        return credentials
    
    async def create_oauth_integration(
        self,
        db: Session,
        name: str,
        integration_type: IntegrationType,
        client_id: str,
        client_secret: str,
        authorization_code: str,
        state: str,
        user_id: int,
        config: Dict[str, Any] = None
    ) -> Integration:
        """Create integration using OAuth flow"""
        
        try:
            # Exchange code for tokens
            token_data = await self.exchange_code_for_token(
                integration_type=integration_type,
                authorization_code=authorization_code,
                client_id=client_id,
                client_secret=client_secret,
                state=state
            )
            
            # Build credentials
            credentials = self.build_oauth_credentials(client_id, client_secret, token_data)
            
            # Use existing integration service to create the integration
            from app.services.integration_service import integration_service
            
            integration = await integration_service.create_integration(
                db=db,
                name=name,
                integration_type=integration_type,
                credentials=credentials,
                config=config,
                user_id=user_id
            )
            
            # Log OAuth creation
            log_event(
                "oauth_integration_created",
                integration_id=integration.id,
                integration_type=integration_type.value,
                user_id=user_id,
                oauth_scopes=token_data.get("scope", "")
            )
            
            return integration
            
        except Exception as e:
            logger.error(f"OAuth integration creation failed: {e}")
            raise

# Global service instance
oauth_service = OAuthService()