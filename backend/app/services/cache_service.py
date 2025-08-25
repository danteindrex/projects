"""
Application-level caching service using Redis
"""
import json
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import timedelta
import asyncio
import functools
import hashlib
import logging
from .redis_service import redis_service

logger = logging.getLogger(__name__)

class CacheService:
    """High-level caching service with advanced features"""
    
    def __init__(self):
        self.redis = redis_service
        self.default_ttl = timedelta(hours=1)
        self.namespace_separator = ":"
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key"""
        return f"{namespace}{self.namespace_separator}{key}"
    
    def _serialize_key_args(self, *args, **kwargs) -> str:
        """Create a cache key from function arguments"""
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if hasattr(arg, '__dict__'):
                # For objects, use their dict representation
                key_parts.append(str(sorted(arg.__dict__.items())))
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        
        # Create hash of the key to avoid very long keys
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._make_key(namespace, key)
        return await self.redis.get(cache_key)
    
    async def set(self, namespace: str, key: str, value: Any, 
                  ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache"""
        cache_key = self._make_key(namespace, key)
        expires = ttl or self.default_ttl
        return await self.redis.set(cache_key, value, expires)
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache"""
        cache_key = self._make_key(namespace, key)
        return await self.redis.delete(cache_key)
    
    async def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._make_key(namespace, key)
        return await self.redis.exists(cache_key)
    
    async def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all keys in a namespace"""
        pattern = f"{namespace}{self.namespace_separator}*"
        keys = await self.redis.get_keys(pattern)
        
        deleted_count = 0
        for key in keys:
            if await self.redis.delete(key):
                deleted_count += 1
        
        return deleted_count
    
    async def get_or_set(self, namespace: str, key: str, factory: Callable,
                         ttl: Optional[timedelta] = None) -> Any:
        """Get from cache or set using factory function"""
        value = await self.get(namespace, key)
        
        if value is not None:
            return value
        
        # Call factory function to get value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache the result
        await self.set(namespace, key, value, ttl)
        return value
    
    def cached(self, namespace: str, ttl: Optional[timedelta] = None):
        """Decorator to cache function results"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Create cache key from function arguments
                cache_key = self._serialize_key_args(*args, **kwargs)
                
                # Try to get from cache
                cached_result = await self.get(namespace, cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call original function
                result = await func(*args, **kwargs)
                
                # Cache the result
                await self.set(namespace, cache_key, result, ttl)
                return result
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we need to run the caching logic in event loop
                # This is a simplified approach - in production you might want a sync cache
                return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    async def increment_counter(self, namespace: str, key: str, 
                              amount: int = 1, ttl: Optional[timedelta] = None) -> Optional[int]:
        """Increment a counter in cache"""
        cache_key = self._make_key(namespace, key)
        result = await self.redis.increment(cache_key, amount)
        
        if result == amount and ttl:  # First increment, set expiration
            await self.redis.expire(cache_key, ttl)
        
        return result
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not await self.redis.is_connected():
            return {"status": "disconnected"}
        
        try:
            # Get all cache keys (be careful in production with large datasets)
            all_keys = await self.redis.get_keys("*")
            
            # Group by namespace
            namespaces = {}
            for key in all_keys:
                if self.namespace_separator in key:
                    namespace = key.split(self.namespace_separator, 1)[0]
                    namespaces[namespace] = namespaces.get(namespace, 0) + 1
            
            return {
                "status": "connected",
                "total_keys": len(all_keys),
                "namespaces": namespaces
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Predefined cache namespaces
class CacheNamespaces:
    """Standard cache namespaces used across the application"""
    USER_DATA = "user"
    INTEGRATION_TEMPLATES = "int_templates"
    INTEGRATION_HEALTH = "int_health"
    INTEGRATION_DATA = "int_data"
    CHAT_SESSIONS = "chat_sessions"
    AUTH_TOKENS = "auth_tokens"
    RATE_LIMITS = "rate_limits"
    SYSTEM_CONFIG = "sys_config"
    API_RESPONSES = "api_responses"

# Global cache service instance
cache_service = CacheService()

# Convenience decorators for common caching patterns
def cache_user_data(ttl: timedelta = timedelta(minutes=15)):
    """Cache user-related data"""
    return cache_service.cached(CacheNamespaces.USER_DATA, ttl)

def cache_integration_data(ttl: timedelta = timedelta(minutes=30)):
    """Cache integration-related data"""
    return cache_service.cached(CacheNamespaces.INTEGRATION_TEMPLATES, ttl)

def cache_api_response(ttl: timedelta = timedelta(minutes=5)):
    """Cache API responses"""
    return cache_service.cached(CacheNamespaces.API_RESPONSES, ttl)