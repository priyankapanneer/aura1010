from app.core.config import settings as app_settings
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.settings import UserSettingsRead, UserSettingsUpdate
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettingsRead)
async def get_settings(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_or_create_default_user()
    user_settings = await repo.get_user_settings(user.id)
    if not user_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return user_settings


@router.patch("", response_model=UserSettingsRead)
async def update_settings(
    updates: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user_id = app_settings.DEFAULT_USER_ID
    updated = await repo.update_user_settings(
        user_id=user_id,
        updates=updates.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Settings not found")
    return updated


@router.get("/integrations")
async def get_integrations_status():
    """Returns provider status without exposing API keys or secrets."""
    has_gemini = bool(app_settings.GEMINI_API_KEY)
    has_openai = bool(app_settings.OPENAI_API_KEY)
    has_anthropic = bool(app_settings.ANTHROPIC_API_KEY)

    return {
        "llm_provider": app_settings.LLM_PROVIDER,
        "llm_model": app_settings.LLM_MODEL,
        "is_mock_llm": app_settings.LLM_PROVIDER == "mock",
        "has_gemini_key": has_gemini,
        "has_openai_key": has_openai,
        "has_anthropic_key": has_anthropic,
        "calendar_provider": app_settings.CALENDAR_PROVIDER,
        "is_simulated_calendar": app_settings.CALENDAR_PROVIDER == "simulated",
        "demo_mode": app_settings.DEMO_MODE,
    }
