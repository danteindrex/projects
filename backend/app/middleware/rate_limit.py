"""
Rate limiting middleware using Redis
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import timedelta
import logging
from ..services.redis_service import rate_limiter
from ..core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window = timedelta(minutes=1)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if (request.url.path.startswith("/health") or 
            request.url.path.startswith("/static") or
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/openapi.json")):
            return await call_next(request)
        
        # Get client identifier (IP address or user ID if authenticated)
        client_ip = self._get_client_ip(request)
        identifier = f"ip:{client_ip}"
        
        # Check if user is authenticated and use user-based limiting
        if hasattr(request.state, "user_id") and request.state.user_id:
            identifier = f"user:{request.state.user_id}"
        
        # Check rate limit
        is_allowed, current_count = await rate_limiter.is_allowed(
            identifier, self.calls_per_minute, self.window
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{self.calls_per_minute}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "60"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls_per_minute - current_count))
        response.headers["X-RateLimit-Reset"] = "60"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP (behind proxy)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"