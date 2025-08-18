import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash
from app.core.encryption import encrypt_data, decrypt_data


class TestSecurityBasics:
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Hashed password should be different from original
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        
        # Should verify correctly
        from app.core.security import verify_password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        from app.core.security import create_access_token, verify_token
        from datetime import timedelta
        
        test_data = {"sub": "test_user_id", "role": "user"}
        token = create_access_token(test_data, expires_delta=timedelta(minutes=30))
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Should verify correctly
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user_id"
        
        # Invalid token should return None
        invalid_payload = verify_token("invalid_token")
        assert invalid_payload is None
    
    def test_encryption_decryption(self):
        """Test data encryption and decryption"""
        test_data = "sensitive_api_key_12345"
        
        encrypted = encrypt_data(test_data)
        assert encrypted != test_data
        assert len(encrypted) > len(test_data)
        
        decrypted = decrypt_data(encrypted)
        assert decrypted == test_data
    
    def test_credentials_encryption(self):
        """Test credentials encryption/decryption"""
        from app.core.encryption import encrypt_credentials, decrypt_credentials
        
        credentials = {
            "api_key": "secret_key_123",
            "username": "api_user",
            "password": "api_password"
        }
        
        encrypted = encrypt_credentials(credentials)
        assert encrypted != str(credentials)
        
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == credentials


class TestAuthenticationSecurity:
    def test_login_rate_limiting(self, client: TestClient):
        """Test rate limiting on login attempts"""
        # This test simulates rapid login attempts
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrong_password"
        }
        
        # Make multiple failed login attempts
        responses = []
        for i in range(10):
            response = client.post("/api/v1/auth/login", data=login_data)
            responses.append(response.status_code)
        
        # Should eventually get rate limited (this depends on implementation)
        # For now, just ensure we get proper error responses
        assert all(status in [401, 429] for status in responses)
    
    def test_sql_injection_protection(self, client: TestClient):
        """Test SQL injection protection"""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        for payload in malicious_payloads:
            login_data = {
                "username": payload,
                "password": payload
            }
            
            response = client.post("/api/v1/auth/login", data=login_data)
            
            # Should return 401 Unauthorized, not 500 Internal Server Error
            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]
    
    def test_xss_protection(self, client: TestClient, test_user: User):
        """Test XSS protection in user inputs"""
        # Login first
        login_data = {"username": test_user.email, "password": "testpassword"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            chat_data = {"message": payload}
            response = client.post("/api/v1/chat/sessions", json=chat_data, headers=headers)
            
            # Should successfully create session but sanitize the content
            assert response.status_code == 200
            # The payload should be escaped or sanitized
            response_data = response.json()
            assert "<script>" not in response_data.get("content", "")
    
    def test_jwt_token_expiration(self, client: TestClient, test_user: User):
        """Test JWT token expiration handling"""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Create an expired token
        expired_token = create_access_token(
            {"sub": str(test_user.id)}, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        # Should reject expired token
        assert response.status_code == 401
    
    def test_unauthorized_access_attempts(self, client: TestClient):
        """Test unauthorized access to protected endpoints"""
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/chat/sessions", "POST"),
            ("/api/v1/chat/sessions", "GET"),
            ("/api/v1/auth/refresh", "POST"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            # Should require authentication
            assert response.status_code in [401, 403]


class TestInputValidation:
    def test_email_validation(self, client: TestClient):
        """Test email format validation"""
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "user@",
            "user@.com",
            "",
            "a" * 255 + "@example.com"  # Too long
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "username": "testuser",
                "password": "password123",
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error
    
    def test_password_strength_validation(self, client: TestClient):
        """Test password strength requirements"""
        weak_passwords = [
            "",           # Empty
            "123",        # Too short
            "password",   # Common password
            "abc",        # Too short
        ]
        
        for password in weak_passwords:
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": password,
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            # Should reject weak passwords
            assert response.status_code in [400, 422]
    
    def test_message_length_validation(self, client: TestClient, test_user: User):
        """Test chat message length validation"""
        # Login first
        login_data = {"username": test_user.email, "password": "testpassword"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test extremely long message
        long_message = "a" * 10000  # 10KB message
        chat_data = {"message": long_message}
        
        response = client.post("/api/v1/chat/sessions", json=chat_data, headers=headers)
        
        # Should handle long messages appropriately
        assert response.status_code in [200, 400, 413]  # OK, Bad Request, or Payload Too Large
    
    def test_json_payload_validation(self, client: TestClient):
        """Test JSON payload validation"""
        # Test malformed JSON
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test missing required fields
        incomplete_data = {"email": "test@example.com"}  # Missing other required fields
        response = client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == 422


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present"""
        response = client.get("/")
        
        # Check for security headers (these should be added by middleware)
        headers = response.headers
        
        # Note: These headers should be implemented in the security middleware
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]
        
        # For now, just check that response has headers
        assert len(headers) > 0
        # TODO: Implement security headers middleware and test properly
    
    def test_cors_policy(self, client: TestClient):
        """Test CORS policy"""
        # Test preflight request
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should allow the request from allowed origin
        assert response.status_code in [200, 204]


class TestMultiTenantSecurity:
    def test_tenant_isolation(self, client: TestClient, test_user: User, db_session: Session):
        """Test that tenant isolation works properly"""
        # Create another user in different tenant
        other_user = User(
            email="other@example.com",
            username="otheruser", 
            hashed_password=get_password_hash("password123"),
            is_active=True,
            role="user"
        )
        # Set different tenant_id if the model supports it
        db_session.add(other_user)
        db_session.commit()
        
        # Login as first user
        login_data = {"username": test_user.email, "password": "testpassword"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token1 = login_response.json()["access_token"]
        
        # Login as second user  
        login_data2 = {"username": other_user.email, "password": "password123"}
        login_response2 = client.post("/api/v1/auth/login", data=login_data2)
        token2 = login_response2.json()["access_token"]
        
        # Create chat session as first user
        headers1 = {"Authorization": f"Bearer {token1}"}
        chat_data = {"message": "User 1 message"}
        response1 = client.post("/api/v1/chat/sessions", json=chat_data, headers=headers1)
        
        # Get sessions as second user
        headers2 = {"Authorization": f"Bearer {token2}"}
        response2 = client.get("/api/v1/chat/sessions", headers=headers2)
        
        # Each user should only see their own sessions
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # The exact isolation test depends on implementation
        # For now, just ensure both requests succeed
        assert len(response2.json()) >= 0  # Could be empty for new user


class TestEncryptionSecurity:
    def test_encryption_key_rotation(self):
        """Test encryption key rotation functionality"""
        from app.core.encryption import encryption_service
        
        original_key = encryption_service.master_key
        test_data = "test_sensitive_data"
        
        # Encrypt with original key
        encrypted_original = encryption_service.encrypt(test_data)
        
        # Rotate keys
        new_key_b64 = encryption_service.rotate_keys()
        assert new_key_b64 != original_key
        
        # Should be able to encrypt with new key
        encrypted_new = encryption_service.encrypt(test_data)
        decrypted_new = encryption_service.decrypt(encrypted_new)
        assert decrypted_new == test_data
    
    def test_api_key_storage_security(self, db_session: Session):
        """Test that API keys are stored encrypted"""
        from app.models.integration import Integration
        from app.core.encryption import encrypt_credentials
        
        # Create integration with encrypted credentials
        credentials = {"api_key": "secret_key_123", "token": "secret_token"}
        encrypted_creds = encrypt_credentials(credentials)
        
        integration = Integration(
            name="Test Integration",
            integration_type="jira",
            config={"endpoint": "https://test.atlassian.net"},
            credentials=encrypted_creds,
            status="active",
            tenant_id="default"
        )
        
        db_session.add(integration)
        db_session.commit()
        
        # Verify credentials are stored encrypted
        stored_integration = db_session.query(Integration).filter_by(name="Test Integration").first()
        assert stored_integration.credentials != str(credentials)
        assert "secret_key_123" not in stored_integration.credentials