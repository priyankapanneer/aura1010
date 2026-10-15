import enum

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(int, enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_duration_minutes = Column(Integer, default=30, nullable=False)
    deadline = Column(DateTime, nullable=True, index=True)
    priority = Column(Integer, default=TaskPriority.MEDIUM.value, nullable=False)
    utility_score = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    mandatory = Column(Boolean, default=False, nullable=False)
    source = Column(String(64), default="user", nullable=False)  # "user", "agent_decomposed", "integration"
    confidence = Column(Float, default=1.0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tasks")
    plan_items = relationship("PlanItem", back_populates="task", cascade="all, delete-orphan")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan",
    )


class TaskDependency(Base, TimestampMixin):
    __tablename__ = "task_dependencies"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="dependents")
