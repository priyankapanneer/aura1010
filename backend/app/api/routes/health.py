from app.core.config import settings
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AURA Planning & Execution Engine",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "calendar_provider": settings.CALENDAR_PROVIDER,
        "demo_mode": settings.DEMO_MODE,
    }
