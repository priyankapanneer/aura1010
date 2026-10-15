from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.repositories.calendar_repo import CalendarRepository
from app.schemas.calendar import CalendarEventCreate, CalendarEventRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEventRead])
async def list_calendar_events(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = CalendarRepository(db)
    user_id = settings.DEFAULT_USER_ID
    events = await repo.list_events(user_id=user_id, start_time=start_time, end_time=end_time)
    return events


@router.post("/events", response_model=CalendarEventRead, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    event_in: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = CalendarRepository(db)
    user_id = settings.DEFAULT_USER_ID
    event = await repo.create_event(user_id=user_id, event_in=event_in)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = CalendarRepository(db)
    user_id = settings.DEFAULT_USER_ID
    deleted = await repo.delete_event(event_id=event_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Calendar event not found")
