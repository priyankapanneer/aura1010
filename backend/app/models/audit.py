import enum

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class ToolExecutionStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class ToolExecutionLog(Base, TimestampMixin):
    __tablename__ = "tool_execution_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    plan_id = Column(String(64), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_name = Column(String(128), nullable=False, index=True)
    input_payload = Column(JSON, nullable=False)
    output_payload = Column(JSON, nullable=True)
    status = Column(Enum(ToolExecutionStatus), default=ToolExecutionStatus.SUCCESS, nullable=False, index=True)
    verified = Column(Boolean, default=False, nullable=False)
    verification_details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    idempotency_key = Column(String(128), nullable=True, index=True)

    # Relationships
    plan = relationship("Plan", back_populates="tool_logs")


class ReplanningAudit(Base, TimestampMixin):
    __tablename__ = "replanning_audits"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    plan_id = Column(String(64), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_reason = Column(String(128), nullable=False)  # "DURATION_EXCEEDED", "TASK_FAILED", "NEW_URGENT_TASK", etc.
    before_summary = Column(Text, nullable=False)
    after_summary = Column(Text, nullable=False)
    changes = Column(JSON, nullable=False)  # Diff details: added, shifted, dropped

    # Relationships
    plan = relationship("Plan", back_populates="replanning_audits")
