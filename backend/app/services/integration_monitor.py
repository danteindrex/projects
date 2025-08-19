"""
Enhanced Integration Monitoring Service with Kafka Streaming
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from app.core.kafka_service import publish_integration_event
from app.models.integration import Integration

logger = logging.getLogger(__name__)

class IntegrationMonitor:
    """Monitor all integration API calls and stream to Kafka"""
    
    @asynccontextmanager
    async def monitor_api_call(
        self, 
        integration: Integration,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ):
        """Context manager to monitor and log API calls"""
        
        start_time = time.time()
        call_id = f"{integration.id}_{int(start_time * 1000)}"
        
        # Sanitize headers (remove sensitive data)
        safe_headers = self._sanitize_headers(headers or {})
        
        # Log API call start
        await publish_integration_event(str(integration.id), "api_call_start", {
            "call_id": call_id,
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "endpoint": endpoint,
            "method": method,
            "params": params or {},
            "headers": safe_headers,
            "timestamp": start_time
        })
        
        try:
            # Yield control to the actual API call
            response_data = {}
            yield response_data
            
            # Calculate timing
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Log successful API call
            await publish_integration_event(str(integration.id), "api_call_success", {
                "call_id": call_id,
                "integration_name": integration.name,
                "integration_type": integration.integration_type.value,
                "endpoint": endpoint,
                "method": method,
                "status_code": response_data.get("status_code", 200),
                "response_size_bytes": response_data.get("response_size", 0),
                "response_time_ms": elapsed_ms,
                "success": True,
                "timestamp": time.time()
            })
            
        except Exception as e:
            # Calculate timing for failed calls
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Determine error type
            error_type = "unknown"
            if "401" in str(e) or "Unauthorized" in str(e):
                error_type = "auth_failure"
            elif "429" in str(e) or "Rate limit" in str(e):
                error_type = "rate_limit"
            elif "timeout" in str(e).lower():
                error_type = "timeout"
            elif "connection" in str(e).lower():
                error_type = "connection_error"
            
            # Log failed API call
            await publish_integration_event(str(integration.id), "api_call_failure", {
                "call_id": call_id,
                "integration_name": integration.name,
                "integration_type": integration.integration_type.value,
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "error_type": error_type,
                "response_time_ms": elapsed_ms,
                "success": False,
                "timestamp": time.time()
            })
            
            # Re-raise the exception
            raise
    
    async def log_integration_health_change(
        self, 
        integration: Integration, 
        old_status: str, 
        new_status: str,
        error_details: Optional[str] = None
    ):
        """Log integration health status changes"""
        await publish_integration_event(str(integration.id), "health_status_change", {
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "old_status": old_status,
            "new_status": new_status,
            "error_details": error_details,
            "timestamp": time.time()
        })
    
    async def log_rate_limit_hit(
        self, 
        integration: Integration,
        endpoint: str,
        retry_after: Optional[int] = None
    ):
        """Log when rate limits are hit"""
        await publish_integration_event(str(integration.id), "rate_limit_hit", {
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "endpoint": endpoint,
            "retry_after_seconds": retry_after,
            "timestamp": time.time()
        })
    
    async def log_authentication_failure(
        self, 
        integration: Integration,
        endpoint: str,
        auth_type: str
    ):
        """Log authentication failures"""
        await publish_integration_event(str(integration.id), "auth_failure", {
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "endpoint": endpoint,
            "auth_type": auth_type,
            "timestamp": time.time()
        })
    
    async def log_data_sync_event(
        self, 
        integration: Integration,
        sync_type: str,  # "pull" or "push"
        records_count: int,
        success: bool,
        error: Optional[str] = None
    ):
        """Log data synchronization events"""
        await publish_integration_event(str(integration.id), "data_sync", {
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "sync_type": sync_type,
            "records_count": records_count,
            "success": success,
            "error": error,
            "timestamp": time.time()
        })
    
    async def log_webhook_received(
        self, 
        integration: Integration,
        webhook_type: str,
        payload_size: int,
        source_ip: str
    ):
        """Log incoming webhooks from integrations"""
        await publish_integration_event(str(integration.id), "webhook_received", {
            "integration_name": integration.name,
            "integration_type": integration.integration_type.value,
            "webhook_type": webhook_type,
            "payload_size_bytes": payload_size,
            "source_ip": source_ip,
            "timestamp": time.time()
        })
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers for logging"""
        sensitive_keys = ['authorization', 'x-api-key', 'cookie', 'x-auth-token']
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized

# Global monitor instance
integration_monitor = IntegrationMonitor()