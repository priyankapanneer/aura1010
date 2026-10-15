from datetime import datetime

from pydantic import BaseModel, Field


class UtilityBreakdown(BaseModel):
    task_id: str
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    importance_score: float = Field(..., ge=0.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    dependency_score: float = Field(..., ge=0.0, le=1.0)
    efficiency_score: float = Field(..., ge=0.0, le=1.0)
    mandatory_bonus: float = Field(0.0, ge=0.0)
    total_utility: float = Field(..., ge=0.0)
    explanation: str


class DecomposedTask(BaseModel):
    id: str | None = None
    title: str = Field(..., min_length=1)
    description: str | None = None
    estimated_duration_minutes: int = Field(30, ge=5, le=1440)
    deadline: datetime | None = None
    priority: int = Field(3, ge=1, le=5)
    mandatory: bool = False
    dependencies: list[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class ScheduleSlot(BaseModel):
    task_id: str
    task_title: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_mandatory: bool
    utility_score: float
    order_index: int


class UnscheduledItem(BaseModel):
    task_id: str
    task_title: str
    reason: str
    hard_conflict: bool
    suggested_alternative: str | None = None


class StructuredGoalParsingOutput(BaseModel):
    understood_goal: str
    is_ambiguous: bool = False
    clarification_question: str | None = None
    extracted_tasks: list[DecomposedTask] = Field(default_factory=list)
    detected_constraints: list[str] = Field(default_factory=list)
    explanation: str
