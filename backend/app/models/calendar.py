from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship


class CalendarEvent(Base, TimestampMixin):
    __tablename__ = "calendar_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    is_fixed = Column(Boolean, default=True, nullable=False)  # Fixed meetings cannot be moved by optimizer
    external_event_id = Column(String(255), nullable=True)
    source = Column(String(64), default="local", nullable=False)  # "local", "simulated", "google"

    # Relationships
    user = relationship("User", back_populates="calendar_events")
