"""
Tests for integration service and endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.integration import Integration, IntegrationType, IntegrationStatus
from app.services.integration_service import IntegrationService, IntegrationTemplates


class TestIntegrationTemplates:
    """Test integration templates functionality"""
    
    def test_jira_template(self):
        """Test Jira integration template"""
        template = IntegrationTemplates.TEMPLATES[IntegrationType.JIRA]
        
        assert template["name"] == "Jira"
        assert template["auth_type"] == "basic"
        assert "domain" in template["required_credentials"]
        assert "email" in template["required_credentials"]
        assert "api_token" in template["required_credentials"]
        assert template["base_url_template"] == "https://{domain}.atlassian.net/rest/api/3"
    
    def test_salesforce_template(self):
        """Test Salesforce integration template"""
        template = IntegrationTemplates.TEMPLATES[IntegrationType.SALESFORCE]
        
        assert template["name"] == "Salesforce"
        assert template["auth_type"] == "oauth2"
        assert "client_id" in template["required_credentials"]
        assert "client_secret" in template["required_credentials"]
        assert template["base_url_template"] == "https://{instance}.salesforce.com"
    
    def test_all_templates_have_required_fields(self):
        """Test all integration templates have required fields"""
        required_fields = ["name", "description", "required_credentials", 
                          "base_url_template", "test_endpoint", "auth_type"]
        
        for integration_type, template in IntegrationTemplates.TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"{integration_type} missing {field}"
            
            # Check required_credentials is a list
            assert isinstance(template["required_credentials"], list)
            assert len(template["required_credentials"]) > 0


class TestIntegrationService:
    """Test integration service functionality"""
    
    def test_get_template_by_type(self):
        """Test getting integration template by type"""
        service = IntegrationService()
        
        template = service.get_template_by_type(IntegrationType.JIRA)
        assert template["name"] == "Jira"
        
        template = service.get_template_by_type(IntegrationType.SALESFORCE)
        assert template["name"] == "Salesforce"
    
    def test_validate_integration_config_jira(self):
        """Test validating Jira integration configuration"""
        service = IntegrationService()
        
        valid_config = {
            "name": "Test Jira",
            "integration_type": IntegrationType.JIRA,
            "credentials": {
                "domain": "testdomain",
                "email": "test@example.com",
                "api_token": "test_token"
            }
        }
        
        # Should not raise exception for valid config
        is_valid, errors = service.validate_integration_config(valid_config)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_integration_config_missing_credentials(self):
        """Test validation with missing credentials"""
        service = IntegrationService()
        
        invalid_config = {
            "name": "Test Jira",
            "integration_type": IntegrationType.JIRA,
            "credentials": {
                "domain": "testdomain",
                # Missing email and api_token
            }
        }
        
        is_valid, errors = service.validate_integration_config(invalid_config)
        assert not is_valid
        assert len(errors) > 0
        assert any("email" in error.lower() for error in errors)
        assert any("api_token" in error.lower() for error in errors)
    
    def test_build_api_url(self):
        """Test building API URLs from templates"""
        service = IntegrationService()
        
        # Test Jira URL building
        jira_url = service.build_api_url(
            IntegrationType.JIRA,
            {"domain": "testcompany"}
        )
        assert jira_url == "https://testcompany.atlassian.net/rest/api/3"
        
        # Test Salesforce URL building
        sf_url = service.build_api_url(
            IntegrationType.SALESFORCE,
            {"instance": "testinstance"}
        )
        assert sf_url == "https://testinstance.salesforce.com"
    
    @patch('app.services.integration_service.aiohttp.ClientSession')
    async def test_test_connection_success(self, mock_session_class):
        """Test successful connection testing"""
        service = IntegrationService()
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        integration = Integration(
            name="Test Integration",
            integration_type=IntegrationType.JIRA,
            base_url="https://test.atlassian.net/rest/api/3",
            encrypted_credentials="encrypted_creds",
            encryption_key_id="test_key"
        )
        
        with patch('app.services.integration_service.decrypt_credentials') as mock_decrypt:
            mock_decrypt.return_value = {
                "domain": "test",
                "email": "test@example.com",
                "api_token": "token123"
            }
            
            success, response_data, error = await service.test_connection(integration)
            
            assert success
            assert response_data == {"success": True}
            assert error is None
    
    @patch('app.services.integration_service.aiohttp.ClientSession')
    async def test_test_connection_failure(self, mock_session_class):
        """Test connection testing failure"""
        service = IntegrationService()
        
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        integration = Integration(
            name="Test Integration",
            integration_type=IntegrationType.JIRA,
            base_url="https://test.atlassian.net/rest/api/3",
            encrypted_credentials="encrypted_creds",
            encryption_key_id="test_key"
        )
        
        with patch('app.services.integration_service.decrypt_credentials') as mock_decrypt:
            mock_decrypt.return_value = {
                "domain": "test",
                "email": "test@example.com",
                "api_token": "invalid_token"
            }
            
            success, response_data, error = await service.test_connection(integration)
            
            assert not success
            assert response_data is None
            assert "401" in error


class TestIntegrationEndpoints:
    """Test integration API endpoints"""
    
    def test_get_integrations_unauthenticated(self, client: TestClient):
        """Test getting integrations without authentication"""
        response = client.get("/api/v1/integrations")
        assert response.status_code == 401
    
    def test_get_integrations_authenticated(self, authenticated_client: TestClient, 
                                         test_integration: Integration):
        """Test getting integrations with authentication"""
        response = authenticated_client.get("/api/v1/integrations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check integration data structure
        integration = data[0]
        assert "id" in integration
        assert "name" in integration
        assert "integration_type" in integration
        assert "status" in integration
    
    def test_create_integration_valid(self, authenticated_client: TestClient):
        """Test creating a valid integration"""
        integration_data = {
            "name": "Test Jira Integration",
            "description": "Integration for testing",
            "integration_type": "jira",
            "base_url": "https://testcompany.atlassian.net/rest/api/3",
            "credentials": {
                "domain": "testcompany",
                "email": "test@example.com",
                "api_token": "test_token_123"
            },
            "config": {
                "default_project": "TEST"
            },
            "rate_limit": 100,
            "timeout": 30
        }
        
        with patch('app.services.integration_service.encrypt_credentials') as mock_encrypt:
            mock_encrypt.return_value = ("encrypted_creds", "key_id")
            
            response = authenticated_client.post(
                "/api/v1/integrations",
                json=integration_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == integration_data["name"]
            assert data["integration_type"] == integration_data["integration_type"]
            assert data["status"] == "testing"  # Default status
    
    def test_create_integration_invalid_type(self, authenticated_client: TestClient):
        """Test creating integration with invalid type"""
        integration_data = {
            "name": "Invalid Integration",
            "integration_type": "invalid_type",
            "base_url": "https://example.com",
            "credentials": {"key": "value"}
        }
        
        response = authenticated_client.post(
            "/api/v1/integrations",
            json=integration_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_integration_missing_credentials(self, authenticated_client: TestClient):
        """Test creating integration with missing required credentials"""
        integration_data = {
            "name": "Incomplete Jira",
            "integration_type": "jira",
            "base_url": "https://test.atlassian.net/rest/api/3",
            "credentials": {
                "domain": "test"
                # Missing email and api_token
            }
        }
        
        response = authenticated_client.post(
            "/api/v1/integrations",
            json=integration_data
        )
        
        assert response.status_code == 400  # Bad request due to validation
    
    def test_test_integration_connection(self, authenticated_client: TestClient,
                                       test_integration: Integration):
        """Test testing integration connection"""
        with patch('app.services.integration_service.IntegrationService.test_connection') as mock_test:
            mock_test.return_value = (True, {"status": "connected"}, None)
            
            response = authenticated_client.post(
                f"/api/v1/integrations/{test_integration.id}/test"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["response_data"]["status"] == "connected"
    
    def test_test_integration_connection_failure(self, authenticated_client: TestClient,
                                               test_integration: Integration):
        """Test integration connection test failure"""
        with patch('app.services.integration_service.IntegrationService.test_connection') as mock_test:
            mock_test.return_value = (False, None, "Connection failed: 401 Unauthorized")
            
            response = authenticated_client.post(
                f"/api/v1/integrations/{test_integration.id}/test"
            )
            
            assert response.status_code == 200  # Still returns 200 but with error info
            data = response.json()
            assert data["success"] == False
            assert "Connection failed" in data["error"]
    
    def test_get_integration_templates(self, authenticated_client: TestClient):
        """Test getting integration templates"""
        response = authenticated_client.get("/api/v1/integrations/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that Jira template exists
        assert "jira" in data
        jira_template = data["jira"]
        assert jira_template["name"] == "Jira"
        assert "required_credentials" in jira_template
    
    def test_get_specific_integration_template(self, authenticated_client: TestClient):
        """Test getting a specific integration template"""
        response = authenticated_client.get("/api/v1/integrations/templates/jira")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jira"
        assert data["auth_type"] == "basic"
        assert "domain" in data["required_credentials"]
    
    def test_get_nonexistent_template(self, authenticated_client: TestClient):
        """Test getting non-existent template"""
        response = authenticated_client.get("/api/v1/integrations/templates/nonexistent")
        
        assert response.status_code == 404
    
    def test_update_integration(self, authenticated_client: TestClient,
                              test_integration: Integration):
        """Test updating an integration"""
        update_data = {
            "name": "Updated Integration Name",
            "description": "Updated description",
            "rate_limit": 200
        }
        
        response = authenticated_client.put(
            f"/api/v1/integrations/{test_integration.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["rate_limit"] == update_data["rate_limit"]
    
    def test_delete_integration(self, authenticated_client: TestClient,
                              test_integration: Integration):
        """Test deleting an integration"""
        response = authenticated_client.delete(
            f"/api/v1/integrations/{test_integration.id}"
        )
        
        assert response.status_code == 200
        
        # Verify integration is deleted
        get_response = authenticated_client.get(f"/api/v1/integrations/{test_integration.id}")
        assert get_response.status_code == 404
    
    def test_integration_health_status(self, authenticated_client: TestClient,
                                     test_integration: Integration):
        """Test getting integration health status"""
        # Update integration with health data
        test_integration.health_status = "healthy"
        test_integration.last_health_check = "2024-01-01T12:00:00Z"
        
        response = authenticated_client.get(
            f"/api/v1/integrations/{test_integration.id}/health"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["health_status"] == "healthy"
        assert data["last_health_check"] is not None


class TestIntegrationSecurity:
    """Test integration security features"""
    
    def test_credentials_not_exposed(self, authenticated_client: TestClient,
                                   test_integration: Integration):
        """Test that credentials are not exposed in API responses"""
        response = authenticated_client.get(f"/api/v1/integrations/{test_integration.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Ensure sensitive data is not exposed
        assert "encrypted_credentials" not in data
        assert "encryption_key_id" not in data
        assert "credentials" not in data
    
    def test_user_can_only_access_own_integrations(self, client: TestClient, 
                                                  test_user: User, test_integration: Integration,
                                                  db_session: Session):
        """Test that users can only access their own integrations"""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed_password",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Login as other user
        login_data = {
            "username": "otheruser",
            "password": "testpassword"
        }
        
        # Mock the password verification for the test
        with patch('app.core.security.verify_password', return_value=True):
            login_response = client.post("/api/v1/auth/login", data=login_data)
            other_token = login_response.json()["access_token"]
        
        # Try to access test_user's integration
        response = client.get(
            f"/api/v1/integrations/{test_integration.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 404  # Should not find integration owned by other user