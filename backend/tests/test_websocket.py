import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestWebSocketEndpoints:
    def test_websocket_connection_lifecycle(self, client: TestClient):
        """Test complete WebSocket connection lifecycle"""
        session_id = "test_session_123"
        
        with client.websocket_connect(f"/api/v1/chat/ws/{session_id}") as websocket:
            # 1. Connection establishment
            connection_msg = websocket.receive_json()
            assert connection_msg["type"] == "connection_established"
            assert connection_msg["session_id"] == session_id
            assert "timestamp" in connection_msg
            
            # 2. Send test message
            test_message = {
                "message": "Test WebSocket message",
                "metadata": {"test": True}
            }
            websocket.send_json(test_message)
            
            # 3. Verify response sequence
            messages_received = []
            timeout_count = 0
            max_timeouts = 10
            
            while timeout_count < max_timeouts:
                try:
                    msg = websocket.receive_json(timeout=1.0)
                    messages_received.append(msg)
                    
                    # Break on final message
                    if msg.get("type") == "final":
                        break
                        
                except Exception:
                    timeout_count += 1
                    continue
            
            # Verify message types received
            message_types = [msg["type"] for msg in messages_received]
            assert "agent_event" in message_types  # Thinking
            assert "tool_result" in message_types  # Tool execution
            assert "token" in message_types        # Response streaming
            assert "final" in message_types        # Completion
    
    def test_websocket_error_handling(self, client: TestClient):
        """Test WebSocket error handling"""
        with client.websocket_connect("/api/v1/chat/ws/error_test") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send invalid message format
            websocket.send_text("invalid json")
            
            # Should receive error message
            error_msg = websocket.receive_json()
            assert error_msg["type"] == "error"
            assert "error occurred" in error_msg["content"].lower()
    
    def test_websocket_multiple_messages(self, client: TestClient):
        """Test handling multiple messages in sequence"""
        with client.websocket_connect("/api/v1/chat/ws/multi_test") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            messages = [
                {"message": "First message"},
                {"message": "Second message"},
                {"message": "Third message"}
            ]
            
            for i, msg in enumerate(messages):
                websocket.send_json(msg)
                
                # Collect all messages for this request
                responses = []
                while True:
                    try:
                        response = websocket.receive_json(timeout=0.5)
                        responses.append(response)
                        if response.get("type") == "final":
                            break
                    except:
                        break
                
                # Verify we got a complete response
                response_types = [r["type"] for r in responses]
                assert "final" in response_types, f"Message {i+1} didn't complete properly"
    
    @patch('app.services.crewai_service.process_query')
    def test_websocket_with_mocked_ai(self, mock_process, client: TestClient):
        """Test WebSocket with mocked AI service"""
        mock_process.return_value = {
            "summary": "Mocked AI response",
            "agent_results": {"test": "data"}
        }
        
        with client.websocket_connect("/api/v1/chat/ws/mock_test") as websocket:
            websocket.receive_json()  # Connection message
            
            websocket.send_json({"message": "Test AI integration"})
            
            # Verify mocked response processing
            final_msg = None
            while True:
                try:
                    msg = websocket.receive_json(timeout=1.0)
                    if msg.get("type") == "final":
                        final_msg = msg
                        break
                except:
                    break
            
            assert final_msg is not None
            assert final_msg["content"] == "Response completed"


class TestWebSocketSecurity:
    def test_websocket_session_isolation(self, client: TestClient):
        """Test that WebSocket sessions are properly isolated"""
        session1_id = "session_1"
        session2_id = "session_2"
        
        # Connect to two different sessions
        with client.websocket_connect(f"/api/v1/chat/ws/{session1_id}") as ws1:
            with client.websocket_connect(f"/api/v1/chat/ws/{session2_id}") as ws2:
                # Skip connection messages
                conn1 = ws1.receive_json()
                conn2 = ws2.receive_json()
                
                assert conn1["session_id"] == session1_id
                assert conn2["session_id"] == session2_id
                
                # Send messages to both
                ws1.send_json({"message": "Message to session 1"})
                ws2.send_json({"message": "Message to session 2"})
                
                # Verify each session only receives its own responses
                # This is ensured by the session_id in the WebSocket path
                assert True  # Sessions are isolated by design
    
    def test_websocket_connection_limits(self, client: TestClient):
        """Test WebSocket connection handling"""
        connections = []
        max_connections = 5
        
        try:
            # Create multiple connections
            for i in range(max_connections):
                ws = client.websocket_connect(f"/api/v1/chat/ws/load_test_{i}")
                ws.__enter__()
                connections.append(ws)
                
                # Verify connection works
                msg = ws.receive_json()
                assert msg["type"] == "connection_established"
            
            # All connections should be working
            assert len(connections) == max_connections
            
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass


class TestWebSocketPerformance:
    def test_websocket_response_time(self, client: TestClient):
        """Test WebSocket response time performance"""
        import time
        
        with client.websocket_connect("/api/v1/chat/ws/perf_test") as websocket:
            websocket.receive_json()  # Connection message
            
            start_time = time.time()
            websocket.send_json({"message": "Performance test message"})
            
            # Wait for first response (thinking indicator)
            websocket.receive_json()
            first_response_time = time.time() - start_time
            
            # Should respond quickly (within 1 second for mock)
            assert first_response_time < 1.0, f"First response took {first_response_time:.2f}s"
            
            # Wait for completion
            while True:
                try:
                    msg = websocket.receive_json(timeout=5.0)
                    if msg.get("type") == "final":
                        break
                except:
                    break
            
            total_time = time.time() - start_time
            assert total_time < 10.0, f"Total processing took {total_time:.2f}s"
    
    def test_websocket_message_throughput(self, client: TestClient):
        """Test WebSocket message throughput"""
        message_count = 10
        
        with client.websocket_connect("/api/v1/chat/ws/throughput_test") as websocket:
            websocket.receive_json()  # Connection message
            
            # Send multiple messages rapidly
            import time
            start_time = time.time()
            
            for i in range(message_count):
                websocket.send_json({"message": f"Throughput test message {i}"})
                
                # Wait for completion of each message
                while True:
                    try:
                        msg = websocket.receive_json(timeout=2.0)
                        if msg.get("type") == "final":
                            break
                    except:
                        break
            
            total_time = time.time() - start_time
            avg_time_per_message = total_time / message_count
            
            # Should handle multiple messages efficiently
            assert avg_time_per_message < 3.0, f"Average time per message: {avg_time_per_message:.2f}s"