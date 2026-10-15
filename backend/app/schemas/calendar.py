from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    is_fixed: bool = True
    external_event_id: str | None = None
    source: str = "local"

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class CalendarEventCreate(CalendarEventBase):
    pass


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_fixed: bool | None = None


class CalendarEventRead(CalendarEventBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
