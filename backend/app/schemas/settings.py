
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UtilityWeightsSchema(BaseModel):
    urgency: float = Field(0.35, ge=0.0, le=1.0)
    importance: float = Field(0.25, ge=0.0, le=1.0)
    impact: float = Field(0.15, ge=0.0, le=1.0)
    dependency: float = Field(0.15, ge=0.0, le=1.0)
    efficiency: float = Field(0.10, ge=0.0, le=1.0)

    @field_validator("efficiency", mode="after")
    def validate_sum(cls, v, info):
        # We allow a small epsilon around 1.0
        data = info.data
        total = data.get("urgency", 0) + data.get("importance", 0) + data.get("impact", 0) + data.get("dependency", 0) + v
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Sum of utility weights must be approximately 1.0 (current sum: {total:.2f})")
        return v


class UserSettingsUpdate(BaseModel):
    work_start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    work_end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    break_duration_minutes: str | None = None
    buffer_minutes_between_tasks: str | None = None
    utility_weights: dict[str, float] | None = None
    demo_mode: bool | None = None
    auto_replan_on_conflict: bool | None = None


class UserSettingsRead(BaseModel):
    id: str
    user_id: str
    work_start_time: str
    work_end_time: str
    break_duration_minutes: str
    buffer_minutes_between_tasks: str
    utility_weights: dict[str, float]
    demo_mode: bool
    auto_replan_on_conflict: bool

    model_config = ConfigDict(from_attributes=True)
