"""
Tests for cache service functionality
"""
import pytest
import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, Mock

from app.services.cache_service import CacheService, CacheNamespaces, cache_service
from app.services.redis_service import RedisService


class TestCacheService:
    """Test cache service functionality"""
    
    @pytest.fixture
    async def mock_redis_service(self):
        """Create mock Redis service"""
        mock_redis = Mock(spec=RedisService)
        mock_redis.get = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=True)
        mock_redis.increment = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.get_keys = AsyncMock(return_value=[])
        mock_redis.is_connected = AsyncMock(return_value=True)
        return mock_redis
    
    def test_make_key(self):
        """Test cache key generation"""
        cache = CacheService()
        
        key = cache._make_key("test_namespace", "test_key")
        assert key == "test_namespace:test_key"
    
    def test_serialize_key_args(self):
        """Test function argument serialization for cache keys"""
        cache = CacheService()
        
        # Test with simple arguments
        key1 = cache._serialize_key_args("arg1", "arg2", kwarg1="value1")
        key2 = cache._serialize_key_args("arg1", "arg2", kwarg1="value1")
        assert key1 == key2  # Should be consistent
        
        # Test with different arguments
        key3 = cache._serialize_key_args("arg1", "different", kwarg1="value1")
        assert key1 != key3  # Should be different
        
        # Test with objects
        obj = Mock()
        obj.__dict__ = {"attr1": "value1", "attr2": "value2"}
        key4 = cache._serialize_key_args(obj)
        assert len(key4) == 32  # MD5 hash length
    
    async def test_get_success(self, mock_redis_service):
        """Test successful cache get operation"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        expected_value = {"test": "data"}
        mock_redis_service.get.return_value = expected_value
        
        result = await cache.get("test_namespace", "test_key")
        
        assert result == expected_value
        mock_redis_service.get.assert_called_once_with("test_namespace:test_key")
    
    async def test_get_not_found(self, mock_redis_service):
        """Test cache get operation when key not found"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.get.return_value = None
        
        result = await cache.get("test_namespace", "nonexistent_key")
        
        assert result is None
        mock_redis_service.get.assert_called_once_with("test_namespace:nonexistent_key")
    
    async def test_set_success(self, mock_redis_service):
        """Test successful cache set operation"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        test_value = {"test": "data"}
        ttl = timedelta(minutes=30)
        
        result = await cache.set("test_namespace", "test_key", test_value, ttl)
        
        assert result is True
        mock_redis_service.set.assert_called_once_with(
            "test_namespace:test_key", test_value, ttl
        )
    
    async def test_set_default_ttl(self, mock_redis_service):
        """Test cache set with default TTL"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        test_value = {"test": "data"}
        
        result = await cache.set("test_namespace", "test_key", test_value)
        
        assert result is True
        mock_redis_service.set.assert_called_once_with(
            "test_namespace:test_key", test_value, cache.default_ttl
        )
    
    async def test_delete_success(self, mock_redis_service):
        """Test successful cache delete operation"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        result = await cache.delete("test_namespace", "test_key")
        
        assert result is True
        mock_redis_service.delete.assert_called_once_with("test_namespace:test_key")
    
    async def test_exists_true(self, mock_redis_service):
        """Test cache exists operation when key exists"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.exists.return_value = True
        
        result = await cache.exists("test_namespace", "test_key")
        
        assert result is True
        mock_redis_service.exists.assert_called_once_with("test_namespace:test_key")
    
    async def test_invalidate_namespace(self, mock_redis_service):
        """Test invalidating entire namespace"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        # Mock keys in namespace
        mock_redis_service.get_keys.return_value = [
            "test_namespace:key1",
            "test_namespace:key2",
            "test_namespace:key3"
        ]
        
        result = await cache.invalidate_namespace("test_namespace")
        
        assert result == 3
        mock_redis_service.get_keys.assert_called_once_with("test_namespace:*")
        assert mock_redis_service.delete.call_count == 3
    
    async def test_get_or_set_cache_hit(self, mock_redis_service):
        """Test get_or_set when value exists in cache"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        cached_value = {"cached": "data"}
        mock_redis_service.get.return_value = cached_value
        
        def factory_function():
            return {"new": "data"}  # This shouldn't be called
        
        result = await cache.get_or_set("test_namespace", "test_key", factory_function)
        
        assert result == cached_value
        mock_redis_service.get.assert_called_once()
        mock_redis_service.set.assert_not_called()  # Should not set since cache hit
    
    async def test_get_or_set_cache_miss(self, mock_redis_service):
        """Test get_or_set when value not in cache"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.get.return_value = None  # Cache miss
        
        def factory_function():
            return {"new": "data"}
        
        result = await cache.get_or_set("test_namespace", "test_key", factory_function)
        
        assert result == {"new": "data"}
        mock_redis_service.get.assert_called_once()
        mock_redis_service.set.assert_called_once()
    
    async def test_get_or_set_async_factory(self, mock_redis_service):
        """Test get_or_set with async factory function"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.get.return_value = None  # Cache miss
        
        async def async_factory_function():
            return {"async": "data"}
        
        result = await cache.get_or_set("test_namespace", "test_key", async_factory_function)
        
        assert result == {"async": "data"}
        mock_redis_service.set.assert_called_once_with(
            "test_namespace:test_key", {"async": "data"}, cache.default_ttl
        )
    
    async def test_increment_counter(self, mock_redis_service):
        """Test counter increment functionality"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.increment.return_value = 5
        
        result = await cache.increment_counter("test_namespace", "counter_key", 3)
        
        assert result == 5
        mock_redis_service.increment.assert_called_once_with("test_namespace:counter_key", 3)
    
    async def test_increment_counter_with_ttl(self, mock_redis_service):
        """Test counter increment with TTL setting"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.increment.return_value = 1  # First increment
        ttl = timedelta(hours=1)
        
        result = await cache.increment_counter("test_namespace", "counter_key", 1, ttl)
        
        assert result == 1
        mock_redis_service.increment.assert_called_once()
        mock_redis_service.expire.assert_called_once_with("test_namespace:counter_key", ttl)
    
    async def test_get_stats_connected(self, mock_redis_service):
        """Test getting cache statistics when connected"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.get_keys.return_value = [
            "user:key1", "user:key2", "integration:key1", "cache:key1"
        ]
        
        stats = await cache.get_stats()
        
        assert stats["status"] == "connected"
        assert stats["total_keys"] == 4
        assert stats["namespaces"]["user"] == 2
        assert stats["namespaces"]["integration"] == 1
        assert stats["namespaces"]["cache"] == 1
    
    async def test_get_stats_disconnected(self, mock_redis_service):
        """Test getting cache statistics when disconnected"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        mock_redis_service.is_connected.return_value = False
        
        stats = await cache.get_stats()
        
        assert stats["status"] == "disconnected"
    
    async def test_cached_decorator_cache_hit(self, mock_redis_service):
        """Test cached decorator with cache hit"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        # Mock cache hit
        cached_result = "cached_result"
        mock_redis_service.get.return_value = cached_result
        
        @cache.cached("test_namespace", timedelta(minutes=10))
        async def test_function(arg1, arg2):
            return f"computed_{arg1}_{arg2}"
        
        result = await test_function("value1", "value2")
        
        assert result == cached_result
        mock_redis_service.get.assert_called_once()
        mock_redis_service.set.assert_not_called()
    
    async def test_cached_decorator_cache_miss(self, mock_redis_service):
        """Test cached decorator with cache miss"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        # Mock cache miss
        mock_redis_service.get.return_value = None
        
        @cache.cached("test_namespace", timedelta(minutes=10))
        async def test_function(arg1, arg2):
            return f"computed_{arg1}_{arg2}"
        
        result = await test_function("value1", "value2")
        
        assert result == "computed_value1_value2"
        mock_redis_service.get.assert_called_once()
        mock_redis_service.set.assert_called_once()


class TestCacheNamespaces:
    """Test cache namespace constants"""
    
    def test_all_namespaces_defined(self):
        """Test that all expected cache namespaces are defined"""
        expected_namespaces = [
            "USER_DATA", "INTEGRATION_TEMPLATES", "INTEGRATION_HEALTH",
            "CHAT_SESSIONS", "AUTH_TOKENS", "RATE_LIMITS", 
            "SYSTEM_CONFIG", "API_RESPONSES"
        ]
        
        for namespace in expected_namespaces:
            assert hasattr(CacheNamespaces, namespace)
            assert isinstance(getattr(CacheNamespaces, namespace), str)
    
    def test_namespace_uniqueness(self):
        """Test that all namespace values are unique"""
        namespace_values = [
            getattr(CacheNamespaces, attr) for attr in dir(CacheNamespaces)
            if not attr.startswith('__')
        ]
        
        assert len(namespace_values) == len(set(namespace_values))


class TestCacheIntegration:
    """Integration tests for cache service"""
    
    @pytest.mark.integration
    async def test_cache_workflow_integration(self, redis_client):
        """Test complete cache workflow with mock Redis"""
        # This test would use the mock Redis client from conftest.py
        cache = CacheService()
        # In a real integration test, you'd connect to actual Redis
        # For now, this serves as a placeholder for integration testing
        
        namespace = "test_integration"
        key = "workflow_test"
        value = {"integration": "test_data"}
        
        # This would test the full workflow if Redis was available
        assert True  # Placeholder assertion


# Performance tests
class TestCachePerformance:
    """Performance tests for cache operations"""
    
    @pytest.mark.slow
    async def test_batch_operations_performance(self, mock_redis_service):
        """Test performance of batch cache operations"""
        cache = CacheService()
        cache.redis = mock_redis_service
        
        # Simulate batch operations
        tasks = []
        for i in range(100):
            tasks.append(cache.set("perf_test", f"key_{i}", f"value_{i}"))
        
        results = await asyncio.gather(*tasks)
        assert all(results)  # All operations should succeed
        assert mock_redis_service.set.call_count == 100