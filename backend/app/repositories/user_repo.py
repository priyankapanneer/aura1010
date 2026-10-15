from typing import Any

from app.core.config import settings
from app.models.user import User, UserSettings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_default_user(self) -> User:
        result = await self.db.execute(select(User).where(User.email == settings.DEFAULT_USER_EMAIL))
        user = result.scalars().first()
        if not user:
            user = User(
                id=settings.DEFAULT_USER_ID,
                email=settings.DEFAULT_USER_EMAIL,
                full_name="AURA Default User",
                timezone="UTC",
            )
            self.db.add(user)
            await self.db.flush()

            user_settings = UserSettings(
                user_id=user.id,
                work_start_time="09:00",
                work_end_time="18:00",
                break_duration_minutes="15",
                buffer_minutes_between_tasks="10",
                utility_weights={
                    "urgency": 0.35,
                    "importance": 0.25,
                    "impact": 0.15,
                    "dependency": 0.15,
                    "efficiency": 0.10,
                },
                demo_mode=settings.DEMO_MODE,
                auto_replan_on_conflict=True,
            )
            self.db.add(user_settings)
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def get_user_settings(self, user_id: str) -> UserSettings | None:
        result = await self.db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        return result.scalars().first()

    async def update_user_settings(self, user_id: str, updates: dict[str, Any]) -> UserSettings | None:
        user_settings = await self.get_user_settings(user_id)
        if not user_settings:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(user_settings, key):
                setattr(user_settings, key, value)
        await self.db.commit()
        await self.db.refresh(user_settings)
        return user_settings
