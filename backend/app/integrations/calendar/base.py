from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class CalendarProvider(ABC):
    @abstractmethod
    async def get_events(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch existing calendar events within window."""

    @abstractmethod
    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a calendar event and return confirmation payload."""

    @abstractmethod
    async def verify_event(
        self,
        user_id: str,
        external_event_id: str,
    ) -> bool:
        """Verify that an event actually exists in the target calendar provider."""
