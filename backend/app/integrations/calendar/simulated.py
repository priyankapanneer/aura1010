import uuid
from datetime import datetime
from typing import Any

from app.integrations.calendar.base import CalendarProvider


class SimulatedCalendarProvider(CalendarProvider):
    """
    Simulated local calendar adapter.
    Stores and validates calendar events in-memory or in database, providing verified confirmations.
    """

    def __init__(self):
        # In-memory registry for verification simulation
        self._events_store: dict[str, dict[str, Any]] = {}

    async def get_events(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        results = []
        for ev in self._events_store.values():
            if ev["user_id"] == user_id and ev["end_time"] >= start_time and ev["start_time"] <= end_time:
                results.append(ev)
        return results

    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        event_id = f"sim_cal_{uuid.uuid4().hex[:12]}"
        event_record = {
            "id": event_id,
            "user_id": user_id,
            "title": title,
            "description": description or "",
            "start_time": start_time,
            "end_time": end_time,
            "is_fixed": True,
            "external_event_id": event_id,
            "source": "simulated_calendar",
            "idempotency_key": idempotency_key,
            "created_at": datetime.now(),
        }
        self._events_store[event_id] = event_record
        return {
            "event_id": event_id,
            "status": "CONFIRMED",
            "provider": "simulated_calendar",
            "verified": True,
            "record": event_record,
        }

    async def verify_event(
        self,
        user_id: str,
        external_event_id: str,
    ) -> bool:
        event = self._events_store.get(external_event_id)
        if not event:
            return False
        return event["user_id"] == user_id


# Global instance for simulated calendar provider
simulated_calendar_provider = SimulatedCalendarProvider()
