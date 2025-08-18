"""Real Integration Service for Business Systems"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import base64

from app.models.integration import Integration, IntegrationType, IntegrationStatus
from app.models.agent import Agent, AgentType, AgentStatus
from app.core.encryption import decrypt_credentials, encrypt_credentials
from app.core.logging import log_event
from app.db.database import get_db_session
from app.services.cache_service import cache_service, CacheNamespaces, cache_integration_data

logger = logging.getLogger(__name__)

class IntegrationTemplates:
    """Templates for different integration types with required fields and API patterns"""
    
    TEMPLATES = {
        IntegrationType.JIRA: {
            "name": "Jira",
            "description": "Atlassian Jira project management and issue tracking",
            "required_credentials": ["domain", "email", "api_token"],
            "base_url_template": "https://{domain}.atlassian.net/rest/api/3",
            "test_endpoint": "/myself",
            "documentation": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/",
            "capabilities": ["issues", "projects", "users", "workflows"],
            "auth_type": "basic"
        },
        IntegrationType.SALESFORCE: {
            "name": "Salesforce",
            "description": "Salesforce CRM platform",
            "required_credentials": ["client_id", "client_secret", "username", "password", "security_token"],
            "base_url_template": "https://{instance}.salesforce.com",
            "test_endpoint": "/services/data/v58.0/sobjects",
            "documentation": "https://developer.salesforce.com/docs/api-explorer",
            "capabilities": ["leads", "accounts", "contacts", "opportunities"],
            "auth_type": "oauth2"
        },
        IntegrationType.ZENDESK: {
            "name": "Zendesk",
            "description": "Zendesk customer support platform",
            "required_credentials": ["subdomain", "email", "api_token"],
            "base_url_template": "https://{subdomain}.zendesk.com/api/v2",
            "test_endpoint": "/users/me",
            "documentation": "https://developer.zendesk.com/api-reference/",
            "capabilities": ["tickets", "users", "organizations", "groups"],
            "auth_type": "basic"
        },
        IntegrationType.GITHUB: {
            "name": "GitHub",
            "description": "GitHub code repository and project management",
            "required_credentials": ["token", "organization"],
            "base_url_template": "https://api.github.com",
            "test_endpoint": "/user",
            "documentation": "https://docs.github.com/en/rest",
            "capabilities": ["repositories", "issues", "pull_requests", "actions"],
            "auth_type": "token"
        },
        IntegrationType.SLACK: {
            "name": "Slack",
            "description": "Slack team communication platform",
            "required_credentials": ["bot_token", "workspace_id"],
            "base_url_template": "https://slack.com/api",
            "test_endpoint": "/auth.test",
            "documentation": "https://api.slack.com/methods",
            "capabilities": ["channels", "messages", "users", "apps"],
            "auth_type": "bearer"
        },
        IntegrationType.HUBSPOT: {
            "name": "HubSpot",
            "description": "HubSpot CRM and marketing platform",
            "required_credentials": ["access_token"],
            "base_url_template": "https://api.hubapi.com",
            "test_endpoint": "/crm/v3/owners",
            "documentation": "https://developers.hubspot.com/docs/api/overview",
            "capabilities": ["contacts", "companies", "deals", "tickets"],
            "auth_type": "bearer"
        },
        IntegrationType.ASANA: {
            "name": "Asana",
            "description": "Asana project management platform",
            "required_credentials": ["access_token"],
            "base_url_template": "https://app.asana.com/api/1.0",
            "test_endpoint": "/users/me",
            "documentation": "https://developers.asana.com/docs",
            "capabilities": ["projects", "tasks", "teams", "users"],
            "auth_type": "bearer"
        },
        IntegrationType.TRELLO: {
            "name": "Trello",
            "description": "Trello project management boards",
            "required_credentials": ["api_key", "token"],
            "base_url_template": "https://api.trello.com/1",
            "test_endpoint": "/members/me",
            "documentation": "https://developer.atlassian.com/cloud/trello/rest/",
            "capabilities": ["boards", "lists", "cards", "members"],
            "auth_type": "key_token"
        },
        IntegrationType.MONDAY: {
            "name": "Monday.com",
            "description": "Monday.com work management platform",
            "required_credentials": ["api_token"],
            "base_url_template": "https://api.monday.com/v2",
            "test_endpoint": "/",
            "documentation": "https://developer.monday.com/api-reference/docs",
            "capabilities": ["boards", "items", "columns", "users"],
            "auth_type": "bearer"
        },
        IntegrationType.CUSTOM: {
            "name": "Custom API",
            "description": "Custom REST API integration",
            "required_credentials": ["api_key"],
            "base_url_template": "{base_url}",
            "test_endpoint": "/health",
            "documentation": "Custom API documentation",
            "capabilities": ["custom_endpoints"],
            "auth_type": "configurable"
        }
    }

class IntegrationService:
    """Service for managing real integrations with business systems"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
    def get_integration_template(self, integration_type: IntegrationType) -> Dict[str, Any]:
        """Get the template configuration for an integration type"""
        return IntegrationTemplates.TEMPLATES.get(integration_type, {})
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available integration templates"""
        return IntegrationTemplates.TEMPLATES
    
    async def test_integration_connection(self, integration: Integration) -> Tuple[bool, str]:
        """Test connection to an integration"""
        try:
            template = self.get_integration_template(integration.integration_type)
            if not template:
                return False, f"Unknown integration type: {integration.integration_type}"
            
            # Decrypt credentials
            credentials = decrypt_credentials(integration.encrypted_credentials)
            
            # Build test URL
            test_url = self._build_api_url(integration.base_url, template["test_endpoint"])
            
            # Make test request
            headers = self._build_auth_headers(template["auth_type"], credentials)
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(test_url, headers=headers) as response:
                    if response.status in [200, 201]:
                        return True, "Connection successful"
                    else:
                        error_text = await response.text()
                        return False, f"Connection failed: HTTP {response.status} - {error_text[:200]}"
                        
        except asyncio.TimeoutError:
            return False, "Connection timeout - please check your network and API endpoints"
        except Exception as e:
            logger.error(f"Integration test failed for {integration.name}: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def create_integration(
        self, 
        db: Session,
        name: str,
        integration_type: IntegrationType,
        credentials: Dict[str, str],
        config: Dict[str, Any] = None,
        user_id: int = None
    ) -> Integration:
        """Create a new integration with real API connection"""
        try:
            template = self.get_integration_template(integration_type)
            if not template:
                raise ValueError(f"Unsupported integration type: {integration_type}")
            
            # Validate required credentials
            missing_creds = []
            for required_field in template["required_credentials"]:
                if required_field not in credentials or not credentials[required_field]:
                    missing_creds.append(required_field)
            
            if missing_creds:
                raise ValueError(f"Missing required credentials: {', '.join(missing_creds)}")
            
            # Build base URL from template
            base_url = self._build_base_url(template["base_url_template"], credentials)
            
            # Encrypt credentials
            encrypted_creds = encrypt_credentials(credentials)
            key_id = "default"  # Use default key ID for now
            
            # Create integration
            integration = Integration(
                name=name,
                description=template["description"],
                integration_type=integration_type,
                base_url=base_url,
                encrypted_credentials=encrypted_creds,
                encryption_key_id=key_id,
                config=config or {},
                status=IntegrationStatus.TESTING,
                owner_id=user_id,
                tenant_id=str(user_id)  # Use user_id as tenant_id for single-tenant setup
            )
            
            db.add(integration)
            db.commit()
            db.refresh(integration)
            
            # Test the connection
            is_connected, test_message = await self.test_integration_connection(integration)
            
            # Update status based on test result
            if is_connected:
                integration.status = IntegrationStatus.ACTIVE
                integration.health_status = "healthy"
                integration.last_health_check = datetime.utcnow().isoformat()
            else:
                integration.status = IntegrationStatus.ERROR
                integration.health_status = "unhealthy"
                integration.last_error = test_message
            
            db.commit()
            
            # Create dedicated AI agent for this integration (optional in development)
            try:
                await self._create_integration_agent(db, integration)
            except Exception as e:
                logger.warning(f"Failed to create agent for integration {integration.name}: {e}")
            
            # Log the integration creation
            log_event(
                "integration_created",
                integration_id=integration.id,
                integration_type=integration_type.value,
                status=integration.status.value,
                user_id=user_id
            )
            
            return integration
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create integration {name}: {e}")
            raise
    
    async def _create_integration_agent(self, db: Session, integration: Integration):
        """Create a CrewAI agent for the integration"""
        try:
            # Import here to avoid circular imports
            from app.services.crewai_service import create_agent_for_integration
            
            # Create actual AI agent using CrewAI service
            agent_id = await create_agent_for_integration(integration)
            
            template = self.get_integration_template(integration.integration_type)
            
            # Create database record for the agent
            agent_config = {
                "crewai_agent_id": agent_id,
                "role": f"{template['name']} Integration Specialist",
                "goal": f"Monitor and manage {template['name']} integration, provide insights and handle queries",
                "backstory": f"I am an AI agent specialized in {template['name']} integration. I can help you monitor your {template['name']} system, retrieve data, and answer questions about your {template['name']} setup.",
                "tools": template.get("capabilities", []),
                "llm_model": "gpt-4-turbo-preview",
                "memory_enabled": True
            }
            
            agent = Agent(
                name=f"{integration.name} Agent",
                description=f"Dedicated AI agent for {integration.name} integration",
                agent_type=AgentType.INTEGRATION,
                status=AgentStatus.ACTIVE,
                integration_id=integration.id,
                config=agent_config,
                capabilities=template.get("capabilities", []),
                tools=template.get("capabilities", [])
            )
            
            db.add(agent)
            db.commit()
            
            logger.info(f"Created CrewAI agent {agent_id} and database record for integration {integration.name}")
            
        except Exception as e:
            logger.warning(f"Failed to create agent for integration {integration.name}: {e}")
            # Don't raise the exception - agent creation is optional
    
    async def update_integration(
        self,
        db: Session,
        integration_id: int,
        name: str = None,
        credentials: Dict[str, str] = None,
        config: Dict[str, Any] = None
    ) -> Integration:
        """Update an existing integration and its associated agent"""
        try:
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                raise ValueError(f"Integration with id {integration_id} not found")
            
            # Update integration fields
            if name:
                integration.name = name
            if credentials:
                integration.encrypted_credentials = encrypt_credentials(credentials)
            if config:
                integration.config = config
            
            integration.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(integration)
            
            # Update the associated CrewAI agent
            from app.services.crewai_service import create_agent_for_integration
            await create_agent_for_integration(integration)  # This will update if exists
            
            logger.info(f"Updated integration {integration.name} and its agent")
            return integration
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update integration {integration_id}: {e}")
            raise
    
    async def delete_integration(self, db: Session, integration_id: int) -> bool:
        """Delete an integration and its associated agent"""
        try:
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                return False
            
            # Remove the associated CrewAI agent
            from app.services.crewai_service import remove_agent_for_integration
            await remove_agent_for_integration(integration_id)
            
            # Delete database records
            db.query(Agent).filter(Agent.integration_id == integration_id).delete()
            db.delete(integration)
            db.commit()
            
            logger.info(f"Deleted integration {integration.name} and its agents")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete integration {integration_id}: {e}")
            raise
    
    def _build_base_url(self, template: str, credentials: Dict[str, str]) -> str:
        """Build base URL from template and credentials"""
        try:
            return template.format(**credentials)
        except KeyError as e:
            raise ValueError(f"Missing credential for URL template: {e}")
    
    def _build_api_url(self, base_url: str, endpoint: str) -> str:
        """Build full API URL"""
        return f"{base_url.rstrip('/')}{endpoint}"
    
    def _build_auth_headers(self, auth_type: str, credentials: Dict[str, str]) -> Dict[str, str]:
        """Build authentication headers based on auth type"""
        headers = {"Content-Type": "application/json"}
        
        if auth_type == "basic":
            if "email" in credentials and "api_token" in credentials:
                auth_string = f"{credentials['email']}:{credentials['api_token']}"
                encoded_auth = base64.b64encode(auth_string.encode()).decode()
                headers["Authorization"] = f"Basic {encoded_auth}"
        
        elif auth_type == "bearer":
            if "access_token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
            elif "bot_token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['bot_token']}"
        
        elif auth_type == "token":
            if "token" in credentials:
                headers["Authorization"] = f"token {credentials['token']}"
        
        elif auth_type == "key_token":
            # For APIs like Trello that use key and token as query params
            pass  # Handled in URL building
        
        elif auth_type == "oauth2":
            # OAuth2 would require a more complex flow
            if "access_token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
        
        return headers
    
    async def fetch_integration_data(
        self, 
        integration: Integration,
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Fetch data from an integration endpoint"""
        try:
            template = self.get_integration_template(integration.integration_type)
            credentials = decrypt_credentials(integration.encrypted_credentials)
            
            # Build URL and headers
            url = self._build_api_url(integration.base_url, endpoint)
            headers = self._build_auth_headers(template["auth_type"], credentials)
            
            # Add query params for key_token auth (like Trello)
            if template["auth_type"] == "key_token" and "api_key" in credentials:
                params = params or {}
                params.update({
                    "key": credentials["api_key"],
                    "token": credentials["token"]
                })
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"API request failed: HTTP {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch data from {integration.name}: {e}")
            raise
    
    async def monitor_integration_health(self, db: Session, integration_id: int):
        """Monitor integration health and update status"""
        try:
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                return
            
            is_healthy, status_message = await self.test_integration_connection(integration)
            
            # Update health status
            integration.last_health_check = datetime.utcnow().isoformat()
            
            if is_healthy:
                integration.health_status = "healthy"
                integration.error_count = 0
                integration.last_error = None
                if integration.status == IntegrationStatus.ERROR:
                    integration.status = IntegrationStatus.ACTIVE
            else:
                integration.health_status = "unhealthy"
                integration.error_count = (integration.error_count or 0) + 1
                integration.last_error = status_message
                
                # Mark as error if too many failures
                if integration.error_count >= 3:
                    integration.status = IntegrationStatus.ERROR
            
            db.commit()
            
            log_event(
                "integration_health_check",
                integration_id=integration.id,
                status=integration.health_status,
                error_count=integration.error_count
            )
            
        except Exception as e:
            logger.error(f"Health monitoring failed for integration {integration_id}: {e}")

# Global service instance
integration_service = IntegrationService()