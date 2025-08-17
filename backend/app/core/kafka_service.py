import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from app.core.config import settings
from app.core.logging import log_kafka_event

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.topic_prefix = settings.KAFKA_TOPIC_PREFIX
        
    async def start_producer(self):
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retry_backoff_ms=500,
                request_timeout_ms=30000,
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop_producer(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def start_consumer(self, topic: str, group_id: str):
        """Start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started for topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop_consumer(self):
        """Stop the Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
    
    async def publish_event(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Publish an event to a Kafka topic"""
        if not self.producer:
            await self.start_producer()
        
        try:
            full_topic = f"{self.topic_prefix}.{topic}"
            await self.producer.send_and_wait(
                topic=full_topic,
                value=message,
                key=key
            )
            log_kafka_event(full_topic, "event_published", message=message)
            logger.debug(f"Event published to topic: {full_topic}")
        except Exception as e:
            logger.error(f"Failed to publish event to topic {topic}: {e}")
            raise
    
    async def publish_integration_event(self, integration_id: str, event_type: str, data: Dict[str, Any]):
        """Publish integration-specific events"""
        message = {
            "event_type": event_type,
            "integration_id": integration_id,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        await self.publish_event("integrations", message, key=integration_id)
    
    async def publish_chat_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Publish chat-related events"""
        message = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        await self.publish_event("chat", message, key=session_id)
    
    async def publish_agent_event(self, agent_id: str, event_type: str, data: Dict[str, Any]):
        """Publish agent-related events"""
        message = {
            "event_type": event_type,
            "agent_id": agent_id,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        await self.publish_event("agents", message, key=agent_id)
    
    async def publish_system_event(self, event_type: str, data: Dict[str, Any]):
        """Publish system-wide events"""
        message = {
            "event_type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        await self.publish_event("system", message)
    
    async def consume_events(self, topic: str, callback):
        """Consume events from a Kafka topic"""
        if not self.consumer:
            await self.start_consumer(topic, f"{self.topic_prefix}-consumer")
        
        try:
            async for message in self.consumer:
                try:
                    await callback(message.value)
                    log_kafka_event(topic, "event_consumed", message=message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise

# Global Kafka service instance
kafka_service = KafkaService()

# Convenience functions
async def publish_event(topic: str, message: Dict[str, Any], key: Optional[str] = None):
    """Convenience function to publish events"""
    await kafka_service.publish_event(topic, message, key)

async def publish_integration_event(integration_id: str, event_type: str, data: Dict[str, Any]):
    """Convenience function to publish integration events"""
    await kafka_service.publish_integration_event(integration_id, event_type, data)

async def publish_chat_event(session_id: str, event_type: str, data: Dict[str, Any]):
    """Convenience function to publish chat events"""
    await kafka_service.publish_chat_event(session_id, event_type, data)

async def publish_agent_event(agent_id: str, event_type: str, data: Dict[str, Any]):
    """Convenience function to publish agent events"""
    await kafka_service.publish_agent_event(agent_id, event_type, data)

async def publish_system_event(event_type: str, data: Dict[str, Any]):
    """Convenience function to publish system events"""
    await kafka_service.publish_system_event(event_type, data)
