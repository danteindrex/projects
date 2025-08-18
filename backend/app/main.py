from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
import structlog

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.logging import setup_logging
from app.middleware.security import (
    SecurityHeadersMiddleware,
    InputSanitizationMiddleware, 
    RequestLoggingMiddleware,
    SecurityEventMiddleware
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.redis_service import redis_service
from app.core.kafka_service import kafka_service

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Create FastAPI app instance first
app = FastAPI(
    title="Business Systems Integration Platform",
    description="AI-Powered Management Platform with Real-Time Integration",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Startup event to initialize Redis
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await redis_service.connect()
        
        # Initialize Kafka producer
        try:
            await kafka_service.start_producer()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.warning(f"Kafka producer failed to start (development mode): {e}")
        
        # Initialize database tables
        from app.db.database import init_db
        init_db()
        
        # Start background monitoring task
        from app.services.monitoring_service import monitoring_task
        asyncio.create_task(monitoring_task())
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        # Don't fail startup if services are not available - graceful degradation
        pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await redis_service.disconnect()
    
    # Stop Kafka producer
    try:
        await kafka_service.stop_producer()
        logger.info("Kafka producer stopped")
    except Exception as e:
        logger.warning(f"Error stopping Kafka producer: {e}")
    
    logger.info("Application shutdown complete")

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityEventMiddleware)

# Request timing middleware (metrics disabled due to psutil dependency)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # TODO: Record metrics when psutil is available
    # from app.services.monitoring_service import metrics_collector
    # metrics_collector.record_request(process_time, response.status_code)
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Business Systems Integration Platform",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
