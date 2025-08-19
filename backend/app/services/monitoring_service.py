"""
Comprehensive monitoring and observability service
"""
import time
import asyncio
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import json
from sqlalchemy import text

from app.core.config import settings
from app.services.redis_service import redis_service
from app.services.cache_service import cache_service, CacheNamespaces
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_percent: float
    disk_used: int
    disk_free: int
    active_connections: int
    request_count: int
    error_count: int
    avg_response_time: float

@dataclass
class HealthStatus:
    """Health status for a service component"""
    name: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.request_times = deque(maxlen=100)
        self.error_count = 0
        self.request_count = 0
        self.start_time = time.time()
    
    def record_request(self, duration: float, status_code: int):
        """Record a request with its duration and status code"""
        self.request_count += 1
        self.request_times.append(duration)
        
        if status_code >= 400:
            self.error_count += 1
    
    def get_avg_response_time(self) -> float:
        """Get average response time from recent requests"""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network connections (simplified)
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_available=memory.available,
                disk_percent=disk.percent,
                disk_used=disk.used,
                disk_free=disk.free,
                active_connections=connections,
                request_count=self.request_count,
                error_count=self.error_count,
                avg_response_time=self.get_avg_response_time()
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Cache recent metrics
            await cache_service.set(
                CacheNamespaces.SYSTEM_CONFIG,
                "latest_metrics",
                asdict(metrics),
                timedelta(minutes=1)
            )
            
            return metrics
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
            raise

class HealthChecker:
    """Health checking for system components"""
    
    def __init__(self):
        self.health_history = defaultdict(list)
        self.alert_thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.1,     # 10%
            "cpu_usage": 80.0,     # 80%
            "memory_usage": 85.0,  # 85%
            "disk_usage": 90.0,    # 90%
        }
    
    async def check_database_health(self) -> HealthStatus:
        """Check database connectivity and performance"""
        start_time = time.time()
        try:
            from app.db.database import get_db
            
            # Simple query to test database
            with get_db() as db:
                result = db.execute(text("SELECT 1")).fetchone()
                if not result:
                    raise Exception("Database query failed")
            
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name="database",
                status="healthy" if response_time < 1.0 else "degraded",
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={"query_result": str(result)}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                name="database",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message=str(e)
            )
        
        await self._record_health_status(status)
        return status
    
    async def check_redis_health(self) -> HealthStatus:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        try:
            # Test Redis connection
            is_connected = await redis_service.is_connected()
            if not is_connected:
                raise Exception("Redis connection failed")
            
            # Test Redis operations
            test_key = "health_check_test"
            await redis_service.set(test_key, "test_value", timedelta(seconds=10))
            test_value = await redis_service.get(test_key)
            await redis_service.delete(test_key)
            
            if test_value != "test_value":
                raise Exception("Redis operation test failed")
            
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name="redis",
                status="healthy" if response_time < 0.5 else "degraded",
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={"test_operation": "success"}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                name="redis",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message=str(e)
            )
        
        await self._record_health_status(status)
        return status
    
    async def check_kafka_health(self) -> HealthStatus:
        """Check Kafka connectivity and performance"""
        start_time = time.time()
        try:
            from app.core.kafka_service import kafka_service
            
            # Check if Kafka producer is available
            if kafka_service.producer is None:
                raise Exception("Kafka producer not initialized")
            
            # Test Kafka operation (lightweight check)
            # We just check if producer is ready
            producer_ready = kafka_service.producer is not None
            
            if not producer_ready:
                raise Exception("Kafka producer not ready")
            
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name="kafka",
                status="healthy" if response_time < 1.0 else "degraded",
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={"producer_ready": producer_ready}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                name="kafka",
                status="degraded",  # Kafka is optional in development
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message=str(e)
            )
        
        await self._record_health_status(status)
        return status
    
    async def check_external_integrations_health(self) -> HealthStatus:
        """Check health of external integrations"""
        start_time = time.time()
        try:
            from app.services.integration_service import IntegrationService
            
            integration_service = IntegrationService()
            # Get summary of integration statuses
            # This would need to be implemented in IntegrationService
            
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name="integrations",
                status="healthy",  # Simplified for now
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={"checked_integrations": 0}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                name="integrations",
                status="degraded",
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message=str(e)
            )
        
        await self._record_health_status(status)
        return status
    
    async def check_system_resources(self) -> HealthStatus:
        """Check system resource usage"""
        start_time = time.time()
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine overall status based on thresholds
            status_level = "healthy"
            issues = []
            
            if cpu_percent > self.alert_thresholds["cpu_usage"]:
                status_level = "degraded"
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > self.alert_thresholds["memory_usage"]:
                status_level = "degraded"
                issues.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > self.alert_thresholds["disk_usage"]:
                status_level = "unhealthy"
                issues.append(f"High disk usage: {disk.percent}%")
            
            response_time = time.time() - start_time
            
            status = HealthStatus(
                name="system_resources",
                status=status_level,
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message="; ".join(issues) if issues else None,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "issues": issues
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                name="system_resources",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_message=str(e)
            )
        
        await self._record_health_status(status)
        return status
    
    async def _record_health_status(self, status: HealthStatus):
        """Record health status in cache and log significant events"""
        # Cache latest status
        await cache_service.set(
            CacheNamespaces.SYSTEM_CONFIG,
            f"health_{status.name}",
            asdict(status),
            timedelta(minutes=5)
        )
        
        # Log status changes
        if status.status != "healthy":
            logger.warning(
                "Health check issue detected",
                component=status.name,
                status=status.status,
                response_time=status.response_time,
                error=status.error_message,
                details=status.details
            )
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        checks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_kafka_health(),
            self.check_system_resources(),
            self.check_external_integrations_health()
        ]
        
        health_results = await asyncio.gather(*checks, return_exceptions=True)
        
        overall_status = "healthy"
        component_statuses = {}
        
        for result in health_results:
            if isinstance(result, Exception):
                overall_status = "unhealthy"
                continue
            
            component_statuses[result.name] = asdict(result)
            
            # Determine overall status
            if result.status == "unhealthy":
                overall_status = "unhealthy"
            elif result.status == "degraded" and overall_status != "unhealthy":
                overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": component_statuses
        }

class AlertManager:
    """Manages alerts and notifications for system issues"""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_history = deque(maxlen=100)
        self.notification_cooldown = timedelta(minutes=10)  # Don't spam alerts
    
    async def check_alerts(self, metrics: SystemMetrics, health_statuses: List[HealthStatus]):
        """Check metrics and health statuses for alert conditions"""
        current_time = datetime.utcnow()
        
        # Check system resource alerts
        await self._check_resource_alerts(metrics, current_time)
        
        # Check component health alerts
        for status in health_statuses:
            await self._check_health_alerts(status, current_time)
    
    async def _check_resource_alerts(self, metrics: SystemMetrics, current_time: datetime):
        """Check for resource-based alerts"""
        alerts = []
        
        if metrics.cpu_percent > 80:
            alerts.append({
                "type": "high_cpu",
                "severity": "warning",
                "message": f"High CPU usage: {metrics.cpu_percent}%",
                "value": metrics.cpu_percent
            })
        
        if metrics.memory_percent > 85:
            alerts.append({
                "type": "high_memory",
                "severity": "critical" if metrics.memory_percent > 95 else "warning",
                "message": f"High memory usage: {metrics.memory_percent}%",
                "value": metrics.memory_percent
            })
        
        if metrics.disk_percent > 90:
            alerts.append({
                "type": "high_disk",
                "severity": "critical",
                "message": f"High disk usage: {metrics.disk_percent}%",
                "value": metrics.disk_percent
            })
        
        for alert in alerts:
            await self._trigger_alert(alert, current_time)
    
    async def _check_health_alerts(self, status: HealthStatus, current_time: datetime):
        """Check for health-based alerts"""
        if status.status in ["degraded", "unhealthy"]:
            alert = {
                "type": f"component_{status.status}",
                "severity": "critical" if status.status == "unhealthy" else "warning",
                "message": f"Component {status.name} is {status.status}: {status.error_message}",
                "component": status.name,
                "error": status.error_message
            }
            await self._trigger_alert(alert, current_time)
    
    async def _trigger_alert(self, alert: Dict[str, Any], current_time: datetime):
        """Trigger an alert if not in cooldown period"""
        alert_key = f"{alert['type']}_{alert.get('component', 'system')}"
        
        # Check if we're in cooldown period for this alert
        if alert_key in self.active_alerts:
            last_alert = self.active_alerts[alert_key]
            if current_time - last_alert < self.notification_cooldown:
                return  # Skip alert due to cooldown
        
        # Record alert
        alert["timestamp"] = current_time.isoformat()
        alert["alert_key"] = alert_key
        
        self.active_alerts[alert_key] = current_time
        self.alert_history.append(alert)
        
        # Log alert
        logger.error(
            "System alert triggered",
            alert_type=alert["type"],
            severity=alert["severity"],
            message=alert["message"],
            **{k: v for k, v in alert.items() if k not in ["type", "severity", "message"]}
        )
        
        # Here you would typically send notifications (email, Slack, etc.)
        # For now, we'll just cache the alert for the dashboard
        await cache_service.set(
            CacheNamespaces.SYSTEM_CONFIG,
            f"alert_{alert_key}",
            alert,
            timedelta(hours=1)
        )

# Global monitoring instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()

# Monitoring background task
async def monitoring_task():
    """Background task to collect metrics and check health"""
    while True:
        try:
            # Collect system metrics
            metrics = await metrics_collector.collect_system_metrics()
            
            # Perform health checks
            health_status = await health_checker.get_overall_health()
            
            # Check for alerts
            component_statuses = [
                HealthStatus(**status) for status in health_status["components"].values()
            ]
            await alert_manager.check_alerts(metrics, component_statuses)
            
            # Log periodic status
            logger.info(
                "System monitoring update",
                cpu_percent=metrics.cpu_percent,
                memory_percent=metrics.memory_percent,
                overall_health=health_status["overall_status"],
                active_connections=metrics.active_connections
            )
            
        except Exception as e:
            logger.error("Error in monitoring task", error=str(e), exc_info=True)
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)