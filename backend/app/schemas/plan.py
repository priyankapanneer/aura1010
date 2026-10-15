from datetime import datetime
from typing import Any

from app.models.plan import ApprovalStatus, PlanStatus
from pydantic import BaseModel, ConfigDict, Field


class PlanGoalRequest(BaseModel):
    goal_prompt: str = Field(..., min_length=3, description="Natural language prompt describing the user's planning goal")
    auto_approve_simulated: bool = Field(False, description="Whether to simulate autonomous approval if in demo mode")


class PlanApprovalAction(BaseModel):
    approved: bool
    response_reason: str | None = None


class PlanReplanRequest(BaseModel):
    trigger_reason: str = Field("USER_REQUESTED", description="Reason for replanning")
    updated_task_id: str | None = None
    new_task_payload: dict[str, Any] | None = None


class PlanItemRead(BaseModel):
    id: str
    task_id: str
    task_title: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    order_index: int
    is_scheduled: bool
    unscheduled_reason: str | None = None
    utility_score: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestRead(BaseModel):
    id: str
    action_type: str
    payload: dict[str, Any]
    status: ApprovalStatus
    response_reason: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ToolExecutionLogRead(BaseModel):
    id: str
    tool_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None = None
    status: str
    verified: bool
    verification_details: dict[str, Any] | None = None
    error_message: str | None = None
    latency_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReplanningAuditRead(BaseModel):
    id: str
    trigger_reason: str
    before_summary: str
    after_summary: str
    changes: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanRead(BaseModel):
    id: str
    user_id: str
    goal_prompt: str
    status: PlanStatus
    version: int
    parent_plan_id: str | None = None
    objective_score: float
    explanation: str | None = None
    items: list[PlanItemRead] = Field(default_factory=list)
    approval_requests: list[ApprovalRequestRead] = Field(default_factory=list)
    tool_logs: list[ToolExecutionLogRead] = Field(default_factory=list)
    replanning_audits: list[ReplanningAuditRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
