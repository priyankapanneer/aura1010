from typing import Any, TypedDict


class AuraState(TypedDict, total=False):
    # Tenant & Run Identity
    user_id: str
    plan_id: str | None
    current_time_iso: str

    # Goal & Understanding
    goal_prompt: str
    is_ambiguous: bool
    clarification_question: str | None

    # Context & Tasks
    user_context: dict[str, Any]
    candidate_tasks: list[dict[str, Any]]
    dependency_graph: dict[str, list[str]]

    # Optimization & Scheduling
    utility_scores: list[dict[str, Any]]
    scheduled_slots: list[dict[str, Any]]
    unscheduled_items: list[dict[str, Any]]
    conflicts: list[str]
    objective_value: float

    # Explanations & Human Review
    explanation: str
    approval_status: str  # "PENDING", "APPROVED", "REJECTED"
    approval_response_reason: str | None
    requires_approval: bool

    # Execution & Verification
    execution_results: list[dict[str, Any]]
    all_executions_verified: bool
    execution_errors: list[str]

    # Replanning
    replanning_trigger: str | None
    is_replanning: bool
    before_plan_summary: str | None
