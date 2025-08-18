"""
Tests for monitoring service and endpoints
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.services.monitoring_service import (
    MetricsCollector,
    HealthChecker,
    AlertManager,
    SystemMetrics,
    HealthStatus
)
from app.models.user import User


class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    def test_record_request(self):
        """Test recording request metrics"""
        collector = MetricsCollector()
        
        # Record some requests
        collector.record_request(0.5, 200)  # Success
        collector.record_request(1.2, 404)  # Client error
        collector.record_request(0.8, 500)  # Server error
        
        assert collector.request_count == 3
        assert collector.error_count == 2  # 404 and 500 are errors
        assert len(collector.request_times) == 3
    
    def test_avg_response_time(self):
        """Test average response time calculation"""
        collector = MetricsCollector()
        
        # Record requests with known durations
        collector.record_request(1.0, 200)
        collector.record_request(2.0, 200)
        collector.record_request(3.0, 200)
        
        avg_time = collector.get_avg_response_time()
        assert avg_time == 2.0  # (1.0 + 2.0 + 3.0) / 3
    
    def test_empty_request_times(self):
        """Test average response time with no requests"""
        collector = MetricsCollector()
        assert collector.get_avg_response_time() == 0.0
    
    @patch('app.services.monitoring_service.psutil.cpu_percent')
    @patch('app.services.monitoring_service.psutil.virtual_memory')
    @patch('app.services.monitoring_service.psutil.disk_usage')
    @patch('app.services.monitoring_service.psutil.net_connections')
    async def test_collect_system_metrics(self, mock_connections, mock_disk, 
                                        mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Mock system data
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(
            percent=60.0, used=8000000000, available=4000000000
        )
        mock_disk.return_value = Mock(
            percent=70.0, used=500000000000, free=200000000000
        )
        mock_connections.return_value = [Mock()] * 5  # 5 connections
        
        collector = MetricsCollector()
        collector.record_request(0.5, 200)
        
        # Mock cache service
        with patch('app.services.monitoring_service.cache_service') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            metrics = await collector.collect_system_metrics()
            
            assert isinstance(metrics, SystemMetrics)
            assert metrics.cpu_percent == 50.0
            assert metrics.memory_percent == 60.0
            assert metrics.disk_percent == 70.0
            assert metrics.active_connections == 5
            assert metrics.request_count == 1
            assert metrics.avg_response_time == 0.5


class TestHealthChecker:
    """Test health checking functionality"""
    
    async def test_check_redis_health_success(self):
        """Test successful Redis health check"""
        health_checker = HealthChecker()
        
        with patch('app.services.monitoring_service.redis_service') as mock_redis:
            mock_redis.is_connected = AsyncMock(return_value=True)
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value="test_value")
            mock_redis.delete = AsyncMock(return_value=True)
            
            with patch('app.services.monitoring_service.cache_service') as mock_cache:
                mock_cache.set = AsyncMock(return_value=True)
                
                status = await health_checker.check_redis_health()
                
                assert status.name == "redis"
                assert status.status == "healthy"
                assert status.response_time < 1.0
                assert status.error_message is None
    
    async def test_check_redis_health_failure(self):
        """Test Redis health check failure"""
        health_checker = HealthChecker()
        
        with patch('app.services.monitoring_service.redis_service') as mock_redis:
            mock_redis.is_connected = AsyncMock(return_value=False)
            
            with patch('app.services.monitoring_service.cache_service') as mock_cache:
                mock_cache.set = AsyncMock(return_value=True)
                
                status = await health_checker.check_redis_health()
                
                assert status.name == "redis"
                assert status.status == "unhealthy"
                assert "Redis connection failed" in status.error_message
    
    async def test_check_database_health_success(self):
        """Test successful database health check"""
        health_checker = HealthChecker()
        
        with patch('app.services.monitoring_service.get_db_session') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.fetchone.return_value = (1,)
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            with patch('app.services.monitoring_service.cache_service') as mock_cache:
                mock_cache.set = AsyncMock(return_value=True)
                
                status = await health_checker.check_database_health()
                
                assert status.name == "database"
                assert status.status in ["healthy", "degraded"]
                assert status.error_message is None
    
    @patch('app.services.monitoring_service.psutil.cpu_percent')
    @patch('app.services.monitoring_service.psutil.virtual_memory')
    @patch('app.services.monitoring_service.psutil.disk_usage')
    async def test_check_system_resources_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test system resources health check - healthy"""
        health_checker = HealthChecker()
        
        # Mock healthy system resources
        mock_cpu.return_value = 50.0  # Below 80% threshold
        mock_memory.return_value = Mock(percent=60.0)  # Below 85% threshold
        mock_disk.return_value = Mock(percent=70.0)  # Below 90% threshold
        
        with patch('app.services.monitoring_service.cache_service') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            status = await health_checker.check_system_resources()
            
            assert status.name == "system_resources"
            assert status.status == "healthy"
            assert status.error_message is None
    
    @patch('app.services.monitoring_service.psutil.cpu_percent')
    @patch('app.services.monitoring_service.psutil.virtual_memory')
    @patch('app.services.monitoring_service.psutil.disk_usage')
    async def test_check_system_resources_degraded(self, mock_disk, mock_memory, mock_cpu):
        """Test system resources health check - degraded"""
        health_checker = HealthChecker()
        
        # Mock degraded system resources
        mock_cpu.return_value = 85.0  # Above 80% threshold
        mock_memory.return_value = Mock(percent=90.0)  # Above 85% threshold
        mock_disk.return_value = Mock(percent=75.0)  # Below 90% threshold
        
        with patch('app.services.monitoring_service.cache_service') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            status = await health_checker.check_system_resources()
            
            assert status.name == "system_resources"
            assert status.status == "degraded"
            assert "High CPU usage" in status.error_message
            assert "High memory usage" in status.error_message


class TestAlertManager:
    """Test alert management functionality"""
    
    async def test_check_resource_alerts(self):
        """Test resource-based alert checking"""
        alert_manager = AlertManager()
        current_time = datetime.utcnow()
        
        # Create metrics that should trigger alerts
        metrics = SystemMetrics(
            timestamp=current_time,
            cpu_percent=85.0,  # Above 80% threshold
            memory_percent=90.0,  # Above 85% threshold
            memory_used=8000000000,
            memory_available=1000000000,
            disk_percent=95.0,  # Above 90% threshold
            disk_used=900000000000,
            disk_free=50000000000,
            active_connections=100,
            request_count=1000,
            error_count=50,
            avg_response_time=1.5
        )
        
        with patch('app.services.monitoring_service.cache_service') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            await alert_manager._check_resource_alerts(metrics, current_time)
            
            # Should have triggered 3 alerts
            assert len(alert_manager.alert_history) == 3
            assert len(alert_manager.active_alerts) == 3
    
    async def test_alert_cooldown(self):
        """Test alert cooldown functionality"""
        alert_manager = AlertManager()
        alert_manager.notification_cooldown = timedelta(seconds=1)  # Short cooldown for test
        
        current_time = datetime.utcnow()
        metrics = SystemMetrics(
            timestamp=current_time,
            cpu_percent=85.0,  # Triggers alert
            memory_percent=50.0,
            memory_used=4000000000,
            memory_available=4000000000,
            disk_percent=50.0,
            disk_used=500000000000,
            disk_free=500000000000,
            active_connections=50,
            request_count=500,
            error_count=10,
            avg_response_time=0.5
        )
        
        with patch('app.services.monitoring_service.cache_service') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            # First alert should be triggered
            await alert_manager._check_resource_alerts(metrics, current_time)
            assert len(alert_manager.alert_history) == 1
            
            # Second alert immediately should be skipped due to cooldown
            await alert_manager._check_resource_alerts(metrics, current_time)
            assert len(alert_manager.alert_history) == 1  # Still only 1
            
            # After cooldown period, should trigger again
            await asyncio.sleep(1.1)  # Wait for cooldown to expire
            future_time = current_time + timedelta(seconds=2)
            await alert_manager._check_resource_alerts(metrics, future_time)
            assert len(alert_manager.alert_history) == 2


class TestMonitoringEndpoints:
    """Test monitoring API endpoints"""
    
    def test_health_check_endpoint(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_detailed_health_check_endpoint(self, client: TestClient):
        """Test detailed health check endpoint"""
        with patch('app.api.api_v1.endpoints.monitoring.health_checker') as mock_checker:
            mock_checker.get_overall_health = AsyncMock(return_value={
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "database": {"status": "healthy", "response_time": 0.1},
                    "redis": {"status": "healthy", "response_time": 0.05}
                }
            })
            
            response = client.get("/api/v1/monitoring/health/detailed")
            assert response.status_code == 200
            data = response.json()
            assert data["overall_status"] == "healthy"
            assert "components" in data
    
    def test_metrics_endpoint(self, client: TestClient):
        """Test system metrics endpoint"""
        with patch('app.api.api_v1.endpoints.monitoring.metrics_collector') as mock_collector:
            mock_metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=50.0,
                memory_percent=60.0,
                memory_used=8000000000,
                memory_available=4000000000,
                disk_percent=70.0,
                disk_used=500000000000,
                disk_free=200000000000,
                active_connections=25,
                request_count=1000,
                error_count=10,
                avg_response_time=0.5
            )
            mock_collector.collect_system_metrics = AsyncMock(return_value=mock_metrics)
            
            response = client.get("/api/v1/monitoring/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["cpu_percent"] == 50.0
            assert data["memory_percent"] == 60.0
            assert "uptime_seconds" in data
    
    def test_alerts_endpoint(self, client: TestClient):
        """Test alerts endpoint"""
        with patch('app.api.api_v1.endpoints.monitoring.alert_manager') as mock_manager:
            mock_manager.active_alerts = {"test_alert": datetime.utcnow()}
            mock_manager.alert_history = [
                {"type": "high_cpu", "severity": "warning", "timestamp": datetime.utcnow().isoformat()}
            ]
            
            response = client.get("/api/v1/monitoring/alerts")
            assert response.status_code == 200
            data = response.json()
            assert data["active_alerts"] == 1
            assert len(data["recent_alerts"]) == 1
    
    def test_cache_stats_admin_required(self, client: TestClient, test_user: User):
        """Test cache stats endpoint requires admin access"""
        # Login as regular user
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/monitoring/cache/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_cache_stats_admin_access(self, admin_client: TestClient):
        """Test cache stats endpoint with admin access"""
        with patch('app.api.api_v1.endpoints.monitoring.cache_service') as mock_cache:
            mock_cache.get_stats = AsyncMock(return_value={
                "status": "connected",
                "total_keys": 100,
                "namespaces": {"user": 50, "integration": 30, "api": 20}
            })
            
            response = admin_client.get("/api/v1/monitoring/cache/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "connected"
            assert data["total_keys"] == 100
    
    def test_clear_cache_admin_required(self, client: TestClient, test_user: User):
        """Test cache clear endpoint requires admin access"""
        # Login as regular user
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/v1/monitoring/cache/clear",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403  # Forbidden for non-admin
    
    def test_prometheus_metrics_endpoint(self, client: TestClient):
        """Test Prometheus metrics endpoint"""
        with patch('app.api.api_v1.endpoints.monitoring.metrics_collector') as mock_collector:
            mock_metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=45.5,
                memory_percent=67.2,
                memory_used=8000000000,
                memory_available=4000000000,
                disk_percent=78.9,
                disk_used=500000000000,
                disk_free=200000000000,
                active_connections=15,
                request_count=2500,
                error_count=25,
                avg_response_time=0.8
            )
            mock_collector.collect_system_metrics = AsyncMock(return_value=mock_metrics)
            
            response = client.get("/api/v1/monitoring/metrics/prometheus")
            assert response.status_code == 200
            
            # Check Prometheus format
            content = response.text
            assert "system_cpu_percent 45.5" in content
            assert "system_memory_percent 67.2" in content
            assert "http_requests_total 2500" in content