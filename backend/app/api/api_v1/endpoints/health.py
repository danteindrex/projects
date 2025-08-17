from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db_session, check_db_connection
from app.core.logging import log_event
import time

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Business Systems Integration Platform"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db_session)):
    """Detailed health check with all dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Business Systems Integration Platform",
        "dependencies": {}
    }
    
    # Check database connection
    try:
        db_healthy = check_db_connection()
        health_status["dependencies"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "details": "PostgreSQL connection"
        }
    except Exception as e:
        health_status["dependencies"]["database"] = {
            "status": "error",
            "details": str(e)
        }
    
    # Check if any dependency is unhealthy
    unhealthy_deps = [
        dep for dep in health_status["dependencies"].values()
        if dep["status"] != "healthy"
    ]
    
    if unhealthy_deps:
        health_status["status"] = "degraded"
        health_status["overall_status"] = "degraded"
    else:
        health_status["overall_status"] = "healthy"
    
    log_event("health_check", status=health_status["overall_status"])
    
    return health_status

@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    return {
        "status": "ready",
        "timestamp": time.time()
    }

@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    return {
        "status": "alive",
        "timestamp": time.time()
    }
