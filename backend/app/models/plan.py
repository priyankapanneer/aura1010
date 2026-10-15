import enum

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class PlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    REPLANNED = "REPLANNED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_prompt = Column(Text, nullable=False)
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    parent_plan_id = Column(String(64), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    objective_score = Column(Float, default=0.0, nullable=False)
    explanation = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    # Relationships
    user = relationship("User", back_populates="plans")
    items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="plan", cascade="all, delete-orphan")
    tool_logs = relationship("ToolExecutionLog", back_populates="plan", cascade="all, delete-orphan")
    replanning_audits = relationship("ReplanningAudit", back_populates="plan", cascade="all, delete-orphan")


class PlanItem(Base, TimestampMixin):
    __tablename__ = "plan_items"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    plan_id = Column(String(64), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_start = Column(DateTime, nullable=True, index=True)
    scheduled_end = Column(DateTime, nullable=True, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    is_scheduled = Column(Boolean, default=True, nullable=False)
    unscheduled_reason = Column(Text, nullable=True)
    utility_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="SCHEDULED", nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="items")
    task = relationship("Task", back_populates="plan_items")


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    plan_id = Column(String(64), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # "CALENDAR_WRITE", "REPLAN_APPLY", "CONSEQUENTIAL_UPDATE"
    payload = Column(JSON, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    response_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    plan = relationship("Plan", back_populates="approval_requests")
