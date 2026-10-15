from datetime import datetime

from app.models.task import TaskPriority, TaskStatus
from pydantic import BaseModel, ConfigDict, Field


class TaskDependencySchema(BaseModel):
    task_id: str
    depends_on_task_id: str


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    estimated_duration_minutes: int = Field(30, ge=5, le=1440, description="Duration in minutes (between 5 and 1440)")
    deadline: datetime | None = None
    priority: int = Field(default=TaskPriority.MEDIUM.value, ge=1, le=5)
    mandatory: bool = False
    source: str = "user"
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class TaskCreate(TaskBase):
    dependencies: list[str] | None = Field(default_factory=list, description="List of task IDs this task depends on")


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    estimated_duration_minutes: int | None = Field(None, ge=5, le=1440)
    deadline: datetime | None = None
    priority: int | None = Field(None, ge=1, le=5)
    status: TaskStatus | None = None
    mandatory: bool | None = None
    utility_score: float | None = None
    dependencies: list[str] | None = None


class TaskRead(TaskBase):
    id: str
    user_id: str
    status: TaskStatus
    utility_score: float
    created_at: datetime
    updated_at: datetime
    dependencies: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
