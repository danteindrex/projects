import structlog
import logging
import sys
from typing import Any, Dict
from app.core.config import settings

def setup_logging():
    """Setup structured logging with structlog"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Create logger instance
    logger = structlog.get_logger()
    logger.info("Logging configured", level=settings.LOG_LEVEL)

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

def log_event(event_type: str, **kwargs):
    """Log a structured event"""
    logger = get_logger()
    logger.info(event_type, **kwargs)

def log_integration_event(integration_id: str, event_type: str, **kwargs):
    """Log integration-specific events"""
    logger = get_logger("integration")
    logger.info(event_type, integration_id=integration_id, **kwargs)

def log_agent_event(agent_id: str, event_type: str, **kwargs):
    """Log agent-specific events"""
    logger = get_logger("agent")
    logger.info(event_type, agent_id=agent_id, **kwargs)

def log_websocket_event(connection_id: str, event_type: str, **kwargs):
    """Log WebSocket-specific events"""
    logger = get_logger("websocket")
    logger.info(event_type, connection_id=connection_id, **kwargs)

def log_kafka_event(topic: str, event_type: str, **kwargs):
    """Log Kafka-specific events"""
    logger = get_logger("kafka")
    logger.info(event_type, topic=topic, **kwargs)

# Context managers for structured logging
class LogContext:
    def __init__(self, logger: structlog.BoundLogger, **context):
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        return self.logger.bind(**self.context)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error("Context exited with exception", 
                            exc_info=(exc_type, exc_val, exc_tb))
        return False

def with_log_context(**context):
    """Decorator to add logging context to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            with LogContext(logger, **context):
                return func(*args, **kwargs)
        return wrapper
    return decorator
