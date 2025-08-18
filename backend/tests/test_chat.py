import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage


class TestChat:
    def test_create_chat_session(self, client: TestClient, test_user: User):
        """Test creating a new chat session"""
        # Login first
        login_data = {"username": test_user.email, "password": "testpassword"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create chat session
        chat_data = {"message": "Hello, this is my first message"}
        response = client.post("/api/v1/chat/sessions", json=chat_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message_id" in data
        assert data["content"] == chat_data["message"]
        assert data["message_type"] == "user"
    
    def test_get_chat_sessions(self, client: TestClient, test_user: User, db_session: Session):
        """Test retrieving user's chat sessions"""
        # Login first
        login_data = {"username": test_user.email, "password": "testpassword"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test session
        chat_session = ChatSession(
            title="Test Session",
            user_id=test_user.id,
            tenant_id="default"
        )
        db_session.add(chat_session)
        db_session.commit()
        
        # Get sessions
        response = client.get("/api/v1/chat/sessions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(session["content"] == "Test Session" for session in data)
    
    def test_unauthorized_chat_access(self, client: TestClient):
        """Test accessing chat endpoints without authentication"""
        response = client.post("/api/v1/chat/sessions", json={"message": "test"})
        assert response.status_code == 403
        
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code == 403


class TestWebSocketChat:
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: TestClient):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/api/v1/chat/ws/test_session") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["session_id"] == "test_session"
    
    @pytest.mark.asyncio
    async def test_websocket_message_processing(self, client: TestClient):
        """Test WebSocket message processing"""
        with client.websocket_connect("/api/v1/chat/ws/test_session") as websocket:
            # Receive connection confirmation
            websocket.receive_json()
            
            # Send a message
            test_message = {"message": "Hello AI"}
            websocket.send_json(test_message)
            
            # Should receive thinking indicator
            thinking_msg = websocket.receive_json()
            assert thinking_msg["type"] == "agent_event"
            assert thinking_msg["content"] == "thinking"
            
            # Should receive tool call events
            tool_msg = websocket.receive_json()
            assert tool_msg["type"] == "agent_event"
            assert tool_msg["metadata"]["event_type"] == "tool_call"
            
            # Should receive tool result
            result_msg = websocket.receive_json()
            assert result_msg["type"] == "tool_result"
            
            # Should receive response tokens
            response_received = False
            final_received = False
            
            for _ in range(50):  # Wait for up to 50 messages
                try:
                    msg = websocket.receive_json(timeout=0.1)
                    if msg["type"] == "token":
                        response_received = True
                    elif msg["type"] == "final":
                        final_received = True
                        break
                except:
                    break
            
            assert response_received, "Should receive response tokens"
            assert final_received, "Should receive final completion message"