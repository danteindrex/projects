from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, integrations, chat, admin, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
