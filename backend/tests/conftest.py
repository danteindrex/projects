"""
Test fixtures and configuration for pytest
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.main import app
from app.models.base import BaseModel
from app.models.user import User, UserRole
from app.models.integration import Integration, IntegrationType, IntegrationStatus
from app.models.chat import ChatSession, ChatMessage
from app.db.database import get_db_session
from app.core.security import get_password_hash
from app.services.redis_service import redis_service


# Test database setup
@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    BaseModel.metadata.create_all(bind=engine)
    
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(test_session_factory):
    """Create test database session"""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Create test client with database session override"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session) -> User:
    """Create a test admin user"""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpassword"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_integration(db_session, test_user) -> Integration:
    """Create a test integration"""
    integration = Integration(
        name="Test Jira Integration",
        description="Test integration for unit tests",
        integration_type=IntegrationType.JIRA,
        base_url="https://test.atlassian.net/rest/api/3",
        status=IntegrationStatus.ACTIVE,
        encrypted_credentials="encrypted_test_credentials",
        encryption_key_id="test_key_id",
        config={"test": "config"},
        owner_id=test_user.id,
        tenant_id=test_user.id
    )
    db_session.add(integration)
    db_session.commit()
    db_session.refresh(integration)
    return integration


@pytest.fixture
def test_chat_session(db_session, test_user) -> ChatSession:
    """Create a test chat session"""
    session = ChatSession(
        title="Test Chat Session",
        status="active",
        user_id=test_user.id,
        tenant_id=test_user.id,
        session_metadata={"test": "metadata"}
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def test_chat_message(db_session, test_chat_session) -> ChatMessage:
    """Create a test chat message"""
    message = ChatMessage(
        content="Test message content",
        message_type="user",
        role="user",
        session_id=test_chat_session.id,
        tenant_id=test_chat_session.tenant_id,
        message_metadata={"test": "message_metadata"}
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


@pytest.fixture
def authenticated_client(client, test_user):
    """Create authenticated test client"""
    # Login to get token
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token_data = response.json()
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
    return client


@pytest.fixture
def admin_client(client, test_admin_user):
    """Create authenticated admin test client"""
    # Login to get token
    login_data = {
        "username": test_admin_user.username,
        "password": "adminpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token_data = response.json()
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
    return client


# Async fixtures for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def redis_client():
    """Mock Redis client for tests"""
    # For tests, we'll use a mock or in-memory implementation
    # to avoid requiring actual Redis instance
    
    class MockRedis:
        def __init__(self):
            self._data = {}
        
        async def get(self, key):
            return self._data.get(key)
        
        async def set(self, key, value, ex=None):
            self._data[key] = value
            return True
        
        async def delete(self, key):
            return self._data.pop(key, None) is not None
        
        async def exists(self, key):
            return key in self._data
        
        async def ping(self):
            return True
        
        async def close(self):
            pass
    
    mock_redis = MockRedis()
    yield mock_redis


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """Create user test data"""
        default_data = {
            "email": "factory@example.com",
            "username": "factoryuser",
            "password": "factorypassword",
            "full_name": "Factory User"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_integration_data(**kwargs):
        """Create integration test data"""
        default_data = {
            "name": "Factory Integration",
            "description": "Test integration from factory",
            "integration_type": "jira",
            "base_url": "https://factory.atlassian.net/rest/api/3",
            "credentials": {
                "domain": "factory",
                "email": "factory@example.com",
                "api_token": "factory_token"
            },
            "config": {"test": "factory_config"}
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_chat_session_data(**kwargs):
        """Create chat session test data"""
        default_data = {
            "title": "Factory Chat Session",
            "metadata": {"test": "factory_metadata"}
        }
        default_data.update(kwargs)
        return default_data


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )