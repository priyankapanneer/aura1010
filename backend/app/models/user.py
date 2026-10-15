from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid
from sqlalchemy import JSON, Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)

    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    work_start_time = Column(String(8), default="09:00", nullable=False)  # HH:MM
    work_end_time = Column(String(8), default="18:00", nullable=False)    # HH:MM
    break_duration_minutes = Column(String(8), default="15", nullable=False)
    buffer_minutes_between_tasks = Column(String(8), default="10", nullable=False)
    utility_weights = Column(
        JSON,
        default=lambda: {
            "urgency": 0.35,
            "importance": 0.25,
            "impact": 0.15,
            "dependency": 0.15,
            "efficiency": 0.10,
        },
        nullable=False,
    )
    demo_mode = Column(Boolean, default=True, nullable=False)
    auto_replan_on_conflict = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="settings")
