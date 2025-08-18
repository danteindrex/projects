import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.kafka_service import KafkaService, kafka_service
from app.core.kafka_service import (
    publish_event,
    publish_integration_event,
    publish_chat_event,
    publish_agent_event,
    publish_system_event
)


class TestKafkaService:
    @pytest.fixture
    def mock_kafka_service(self):
        """Create a mock Kafka service for testing"""
        service = KafkaService()
        service.producer = AsyncMock()
        service.consumer = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_start_producer(self, mock_kafka_service):
        """Test Kafka producer startup"""
        # Mock the AIOKafkaProducer
        with patch('app.core.kafka_service.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            await mock_kafka_service.start_producer()
            
            mock_producer.start.assert_called_once()
            assert mock_kafka_service.producer == mock_producer
    
    @pytest.mark.asyncio
    async def test_publish_event(self, mock_kafka_service):
        """Test publishing events to Kafka"""
        test_message = {"test": "data", "timestamp": "2023-01-01T00:00:00"}
        test_topic = "test_topic"
        test_key = "test_key"
        
        mock_kafka_service.producer.send_and_wait = AsyncMock()
        
        await mock_kafka_service.publish_event(test_topic, test_message, test_key)
        
        mock_kafka_service.producer.send_and_wait.assert_called_once_with(
            topic=f"{mock_kafka_service.topic_prefix}.{test_topic}",
            value=test_message,
            key=test_key
        )
    
    @pytest.mark.asyncio
    async def test_publish_integration_event(self, mock_kafka_service):
        """Test publishing integration-specific events"""
        integration_id = "test_integration"
        event_type = "api_call"
        data = {"status": "success", "response_time": 123}
        
        mock_kafka_service.publish_event = AsyncMock()
        
        await mock_kafka_service.publish_integration_event(integration_id, event_type, data)
        
        mock_kafka_service.publish_event.assert_called_once()
        call_args = mock_kafka_service.publish_event.call_args
        
        assert call_args[0][0] == "integrations"  # topic
        message = call_args[0][1]  # message
        assert message["event_type"] == event_type
        assert message["integration_id"] == integration_id
        assert message["data"] == data
        assert call_args[1]["key"] == integration_id
    
    @pytest.mark.asyncio
    async def test_publish_chat_event(self, mock_kafka_service):
        """Test publishing chat-related events"""
        session_id = "test_session"
        event_type = "message_sent"
        data = {"message": "Hello", "user_id": "user123"}
        
        mock_kafka_service.publish_event = AsyncMock()
        
        await mock_kafka_service.publish_chat_event(session_id, event_type, data)
        
        mock_kafka_service.publish_event.assert_called_once()
        call_args = mock_kafka_service.publish_event.call_args
        
        assert call_args[0][0] == "chat"
        message = call_args[0][1]
        assert message["event_type"] == event_type
        assert message["session_id"] == session_id
        assert message["data"] == data
        assert call_args[1]["key"] == session_id
    
    @pytest.mark.asyncio
    async def test_publish_agent_event(self, mock_kafka_service):
        """Test publishing agent-related events"""
        agent_id = "test_agent"
        event_type = "task_completed"
        data = {"result": "success", "duration": 456}
        
        mock_kafka_service.publish_event = AsyncMock()
        
        await mock_kafka_service.publish_agent_event(agent_id, event_type, data)
        
        mock_kafka_service.publish_event.assert_called_once()
        call_args = mock_kafka_service.publish_agent_event.call_args
        
        assert call_args[0][0] == "agents"
        message = call_args[0][1]
        assert message["event_type"] == event_type
        assert message["agent_id"] == agent_id
        assert message["data"] == data
        assert call_args[1]["key"] == agent_id
    
    @pytest.mark.asyncio
    async def test_publish_system_event(self, mock_kafka_service):
        """Test publishing system-wide events"""
        event_type = "system_startup"
        data = {"version": "1.0.0", "environment": "test"}
        
        mock_kafka_service.publish_event = AsyncMock()
        
        await mock_kafka_service.publish_system_event(event_type, data)
        
        mock_kafka_service.publish_event.assert_called_once()
        call_args = mock_kafka_service.publish_event.call_args
        
        assert call_args[0][0] == "system"
        message = call_args[0][1]
        assert message["event_type"] == event_type
        assert message["data"] == data
    
    @pytest.mark.asyncio
    async def test_consume_events(self, mock_kafka_service):
        """Test consuming events from Kafka"""
        test_topic = "test_topic"
        
        # Mock consumer messages
        mock_message1 = MagicMock()
        mock_message1.value = {"event": "test1"}
        mock_message2 = MagicMock()
        mock_message2.value = {"event": "test2"}
        
        mock_kafka_service.consumer.__aiter__ = AsyncMock(return_value=iter([mock_message1, mock_message2]))
        
        # Mock callback
        callback = AsyncMock()
        
        # Consume a limited number of messages
        async def limited_consume():
            count = 0
            async for message in mock_kafka_service.consumer:
                await callback(message.value)
                count += 1
                if count >= 2:
                    break
        
        await limited_consume()
        
        assert callback.call_count == 2
        callback.assert_any_call({"event": "test1"})
        callback.assert_any_call({"event": "test2"})
    
    @pytest.mark.asyncio
    async def test_kafka_error_handling(self, mock_kafka_service):
        """Test Kafka error handling"""
        mock_kafka_service.producer.send_and_wait = AsyncMock(side_effect=Exception("Kafka error"))
        
        with pytest.raises(Exception, match="Kafka error"):
            await mock_kafka_service.publish_event("test_topic", {"test": "data"})
    
    @pytest.mark.asyncio
    async def test_start_consumer(self, mock_kafka_service):
        """Test Kafka consumer startup"""
        test_topic = "test_topic"
        test_group_id = "test_group"
        
        with patch('app.core.kafka_service.AIOKafkaConsumer') as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            
            await mock_kafka_service.start_consumer(test_topic, test_group_id)
            
            mock_consumer.start.assert_called_once()
            assert mock_kafka_service.consumer == mock_consumer
    
    @pytest.mark.asyncio
    async def test_stop_producer(self, mock_kafka_service):
        """Test stopping Kafka producer"""
        mock_kafka_service.producer = AsyncMock()
        
        await mock_kafka_service.stop_producer()
        
        mock_kafka_service.producer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_consumer(self, mock_kafka_service):
        """Test stopping Kafka consumer"""
        mock_kafka_service.consumer = AsyncMock()
        
        await mock_kafka_service.stop_consumer()
        
        mock_kafka_service.consumer.stop.assert_called_once()


class TestKafkaConvenienceFunctions:
    @pytest.mark.asyncio
    async def test_convenience_publish_functions(self):
        """Test all convenience publish functions"""
        with patch.object(kafka_service, 'publish_event') as mock_publish, \
             patch.object(kafka_service, 'publish_integration_event') as mock_pub_int, \
             patch.object(kafka_service, 'publish_chat_event') as mock_pub_chat, \
             patch.object(kafka_service, 'publish_agent_event') as mock_pub_agent, \
             patch.object(kafka_service, 'publish_system_event') as mock_pub_system:
            
            # Test generic publish
            await publish_event("topic", {"data": "test"}, "key")
            mock_publish.assert_called_once_with("topic", {"data": "test"}, "key")
            
            # Test integration publish
            await publish_integration_event("int1", "event", {"data": "test"})
            mock_pub_int.assert_called_once_with("int1", "event", {"data": "test"})
            
            # Test chat publish
            await publish_chat_event("session1", "event", {"data": "test"})
            mock_pub_chat.assert_called_once_with("session1", "event", {"data": "test"})
            
            # Test agent publish
            await publish_agent_event("agent1", "event", {"data": "test"})
            mock_pub_agent.assert_called_once_with("agent1", "event", {"data": "test"})
            
            # Test system publish
            await publish_system_event("event", {"data": "test"})
            mock_pub_system.assert_called_once_with("event", {"data": "test"})


class TestKafkaIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_kafka_flow(self):
        """Test end-to-end Kafka message flow"""
        # This would require a real Kafka instance for full integration testing
        # For now, we'll test the message structure and flow with mocks
        
        with patch.object(kafka_service, 'producer') as mock_producer:
            mock_producer.send_and_wait = AsyncMock()
            
            # Simulate a chat event flow
            session_id = "test_session_123"
            user_message = "Hello AI assistant"
            
            # Publish chat start event
            await publish_chat_event(session_id, "chat_started", {
                "user_message": user_message,
                "timestamp": "2023-01-01T00:00:00"
            })
            
            # Publish agent processing event
            await publish_agent_event("router_001", "processing_started", {
                "session_id": session_id,
                "query": user_message
            })
            
            # Publish integration call event
            await publish_integration_event("jira_integration", "api_call_started", {
                "session_id": session_id,
                "endpoint": "/api/issues"
            })
            
            # Verify all events were published
            assert mock_producer.send_and_wait.call_count == 3
            
            # Verify topic names and message structure
            calls = mock_producer.send_and_wait.call_args_list
            
            # Chat event
            chat_call = calls[0]
            assert "chat" in chat_call[1]["topic"]
            assert chat_call[1]["value"]["event_type"] == "chat_started"
            assert chat_call[1]["key"] == session_id
            
            # Agent event
            agent_call = calls[1]
            assert "agents" in agent_call[1]["topic"]
            assert agent_call[1]["value"]["event_type"] == "processing_started"
            assert agent_call[1]["key"] == "router_001"
            
            # Integration event
            int_call = calls[2]
            assert "integrations" in int_call[1]["topic"]
            assert int_call[1]["value"]["event_type"] == "api_call_started"
            assert int_call[1]["key"] == "jira_integration"