from datetime import datetime

from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventCreate, CalendarEventUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class CalendarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_events(
        self,
        user_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[CalendarEvent]:
        query = select(CalendarEvent).where(CalendarEvent.user_id == user_id).order_by(CalendarEvent.start_time.asc())
        if start_time:
            query = query.where(CalendarEvent.end_time >= start_time)
        if end_time:
            query = query.where(CalendarEvent.start_time <= end_time)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_event(self, event_id: str, user_id: str) -> CalendarEvent | None:
        query = select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_event(self, user_id: str, event_in: CalendarEventCreate) -> CalendarEvent:
        event = CalendarEvent(
            user_id=user_id,
            title=event_in.title,
            description=event_in.description,
            start_time=event_in.start_time,
            end_time=event_in.end_time,
            is_fixed=event_in.is_fixed,
            external_event_id=event_in.external_event_id,
            source=event_in.source,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def update_event(self, event_id: str, user_id: str, updates: CalendarEventUpdate) -> CalendarEvent | None:
        event = await self.get_event(event_id, user_id)
        if not event:
            return None

        update_dict = updates.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(event, key, value)

        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def delete_event(self, event_id: str, user_id: str) -> bool:
        event = await self.get_event(event_id, user_id)
        if not event:
            return False
        await self.db.delete(event)
        await self.db.commit()
        return True
