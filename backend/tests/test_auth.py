import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash


class TestAuth:
    def test_register_user(self, client: TestClient, db_session: Session):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "testpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert data["role"] == "user"
    
    def test_register_duplicate_user(self, client: TestClient, test_user: User):
        """Test registering duplicate user fails"""
        user_data = {
            "email": test_user.email,
            "username": test_user.username,
            "password": "testpassword123",
            "full_name": "Duplicate User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_login_valid_credentials(self, client: TestClient, test_user: User):
        """Test login with valid credentials"""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials"""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient, test_user: User):
        """Test getting current user info"""
        # First login to get token
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_refresh_token(self, client: TestClient, test_user: User):
        """Test token refresh"""
        # First login to get token
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Refresh token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403
    
    def test_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401