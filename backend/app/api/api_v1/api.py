from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, integrations, chat, health  # Temporarily disabled: admin, monitoring

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
# Temporarily disabled: admin, monitoring
