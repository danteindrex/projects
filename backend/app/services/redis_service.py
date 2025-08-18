"""
Redis service for caching and session management
"""
import json
import redis.asyncio as redis
from typing import Optional, Any, Dict, List
from datetime import timedelta
import pickle
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for caching and session management"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # Handle binary data
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self._redis or not self._connected:
            return False
        try:
            await self._redis.ping()
            return True
        except:
            self._connected = False
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            
            # Try to unpickle first, fallback to string
            try:
                return pickle.loads(value)
            except:
                return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, expires: Optional[timedelta] = None) -> bool:
        """Set value in Redis"""
        if not await self.is_connected():
            return False
        
        try:
            # Serialize complex objects with pickle
            if isinstance(value, (dict, list, tuple, set)):
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value).encode('utf-8')
            
            if expires:
                await self._redis.setex(key, expires, serialized_value)
            else:
                await self._redis.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not await self.is_connected():
            return False
        
        try:
            return bool(await self._redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key} in Redis: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a value in Redis"""
        if not await self.is_connected():
            return None
        
        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in Redis: {e}")
            return None
    
    async def expire(self, key: str, expires: timedelta) -> bool:
        """Set expiration for a key"""
        if not await self.is_connected():
            return False
        
        try:
            return await self._redis.expire(key, expires)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key} in Redis: {e}")
            return False
    
    async def get_keys(self, pattern: str) -> List[str]:
        """Get all keys matching pattern"""
        if not await self.is_connected():
            return []
        
        try:
            keys = await self._redis.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern} from Redis: {e}")
            return []

class SessionManager:
    """Session management using Redis"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.default_expiry = timedelta(hours=24)
    
    async def create_session(self, user_id: int, session_data: Dict[str, Any], 
                           expires: Optional[timedelta] = None) -> str:
        """Create a new session"""
        import uuid
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_prefix}{session_id}"
        
        # Add metadata to session
        session_data.update({
            "user_id": user_id,
            "created_at": json.dumps({}, default=str),
            "last_accessed": json.dumps({}, default=str)
        })
        
        expires = expires or self.default_expiry
        success = await self.redis.set(session_key, session_data, expires)
        
        if success:
            # Track user sessions
            await self._add_user_session(user_id, session_id)
        
        return session_id if success else None
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            # Update last accessed time
            session_data["last_accessed"] = json.dumps({}, default=str)
            await self.redis.set(session_key, session_data, self.default_expiry)
        
        return session_data
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"{self.session_prefix}{session_id}"
        current_data = await self.redis.get(session_key)
        
        if current_data:
            current_data.update(data)
            current_data["last_accessed"] = json.dumps({}, default=str)
            return await self.redis.set(session_key, current_data, self.default_expiry)
        
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.session_prefix}{session_id}"
        session_data = await self.redis.get(session_key)
        
        if session_data and "user_id" in session_data:
            await self._remove_user_session(session_data["user_id"], session_id)
        
        return await self.redis.delete(session_key)
    
    async def get_user_sessions(self, user_id: int) -> List[str]:
        """Get all sessions for a user"""
        key = f"{self.user_sessions_prefix}{user_id}"
        sessions = await self.redis.get(key)
        return sessions if sessions else []
    
    async def delete_all_user_sessions(self, user_id: int) -> bool:
        """Delete all sessions for a user"""
        sessions = await self.get_user_sessions(user_id)
        success = True
        
        for session_id in sessions:
            if not await self.delete_session(session_id):
                success = False
        
        # Clean up user sessions list
        await self.redis.delete(f"{self.user_sessions_prefix}{user_id}")
        return success
    
    async def _add_user_session(self, user_id: int, session_id: str):
        """Add session to user's session list"""
        key = f"{self.user_sessions_prefix}{user_id}"
        sessions = await self.redis.get(key) or []
        
        if session_id not in sessions:
            sessions.append(session_id)
            await self.redis.set(key, sessions, timedelta(days=7))
    
    async def _remove_user_session(self, user_id: int, session_id: str):
        """Remove session from user's session list"""
        key = f"{self.user_sessions_prefix}{user_id}"
        sessions = await self.redis.get(key)
        
        if sessions and session_id in sessions:
            sessions.remove(session_id)
            if sessions:
                await self.redis.set(key, sessions, timedelta(days=7))
            else:
                await self.redis.delete(key)

class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.rate_limit_prefix = "rate_limit:"
    
    async def is_allowed(self, identifier: str, limit: int, window: timedelta) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        Returns: (is_allowed, current_count)
        """
        key = f"{self.rate_limit_prefix}{identifier}"
        
        if not await self.redis.is_connected():
            # Allow if Redis is down (fail open)
            return True, 0
        
        try:
            current_count = await self.redis.increment(key)
            
            if current_count == 1:
                # First request in window, set expiration
                await self.redis.expire(key, window)
            
            return current_count <= limit, current_count
        except Exception as e:
            logger.error(f"Rate limit check failed for {identifier}: {e}")
            # Fail open
            return True, 0
    
    async def reset_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier"""
        key = f"{self.rate_limit_prefix}{identifier}"
        return await self.redis.delete(key)

# Global instances
redis_service = RedisService()
session_manager = SessionManager(redis_service)
rate_limiter = RateLimiter(redis_service)