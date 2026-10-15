import asyncio
import json

from app.agents.planner import PlannerService
from app.core.config import settings
from app.core.database import get_db
from app.repositories.plan_repo import PlanRepository
from app.schemas.plan import (
    ApprovalRequestRead,
    PlanApprovalAction,
    PlanGoalRequest,
    PlanItemRead,
    PlanRead,
    PlanReplanRequest,
    ReplanningAuditRead,
    ToolExecutionLogRead,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/plans", tags=["plans"])


def format_plan_read(plan) -> PlanRead:
    items = []
    for it in plan.items:
        items.append(
            PlanItemRead(
                id=it.id,
                task_id=it.task_id,
                task_title=it.task.title if it.task else "Task",
                scheduled_start=it.scheduled_start,
                scheduled_end=it.scheduled_end,
                order_index=it.order_index,
                is_scheduled=it.is_scheduled,
                unscheduled_reason=it.unscheduled_reason,
                utility_score=it.utility_score,
                status=it.status,
            )
        )

    approvals = [
        ApprovalRequestRead(
            id=a.id,
            action_type=a.action_type,
            payload=a.payload,
            status=a.status,
            response_reason=a.response_reason,
            created_at=a.created_at,
            resolved_at=a.resolved_at,
        )
        for a in plan.approval_requests
    ]

    tool_logs = [
        ToolExecutionLogRead(
            id=log_entry.id,
            tool_name=log_entry.tool_name,
            input_payload=log_entry.input_payload,
            output_payload=log_entry.output_payload,
            status=log_entry.status.value if hasattr(log_entry.status, "value") else str(log_entry.status),
            verified=log_entry.verified,
            verification_details=log_entry.verification_details,
            error_message=log_entry.error_message,
            latency_ms=log_entry.latency_ms,
            created_at=log_entry.created_at,
        )
        for log_entry in plan.tool_logs
    ]

    audits = [
        ReplanningAuditRead(
            id=au.id,
            trigger_reason=au.trigger_reason,
            before_summary=au.before_summary,
            after_summary=au.after_summary,
            changes=au.changes,
            created_at=au.created_at,
        )
        for au in plan.replanning_audits
    ]

    return PlanRead(
        id=plan.id,
        user_id=plan.user_id,
        goal_prompt=plan.goal_prompt,
        status=plan.status,
        version=plan.version,
        parent_plan_id=plan.parent_plan_id,
        objective_score=plan.objective_score,
        explanation=plan.explanation,
        items=items,
        approval_requests=approvals,
        tool_logs=tool_logs,
        replanning_audits=audits,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def generate_plan(
    req: PlanGoalRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PlannerService(db)
    user_id = settings.DEFAULT_USER_ID
    res = await service.generate_plan(
        user_id=user_id,
        goal_prompt=req.goal_prompt,
        auto_approve_simulated=req.auto_approve_simulated,
    )

    if res.get("plan_id"):
        repo = PlanRepository(db)
        plan = await repo.get_plan(res["plan_id"], user_id)
        if plan:
            return format_plan_read(plan)

    return res


@router.get("", response_model=list[PlanRead])
async def list_plans(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    repo = PlanRepository(db)
    user_id = settings.DEFAULT_USER_ID
    plans = await repo.list_plans(user_id=user_id, limit=limit)
    return [format_plan_read(p) for p in plans]


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = PlanRepository(db)
    user_id = settings.DEFAULT_USER_ID
    plan = await repo.get_plan(plan_id, user_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return format_plan_read(plan)


@router.post("/{plan_id}/approve", response_model=PlanRead)
async def approve_plan(
    plan_id: str,
    action: PlanApprovalAction,
    db: AsyncSession = Depends(get_db),
):
    service = PlannerService(db)
    user_id = settings.DEFAULT_USER_ID
    await service.handle_approval_decision(
        user_id=user_id,
        plan_id=plan_id,
        approved=True,
        response_reason=action.response_reason or "Approved by user",
    )
    repo = PlanRepository(db)
    updated = await repo.get_plan(plan_id, user_id)
    return format_plan_read(updated)


@router.post("/{plan_id}/reject", response_model=PlanRead)
async def reject_plan(
    plan_id: str,
    action: PlanApprovalAction,
    db: AsyncSession = Depends(get_db),
):
    service = PlannerService(db)
    user_id = settings.DEFAULT_USER_ID
    await service.handle_approval_decision(
        user_id=user_id,
        plan_id=plan_id,
        approved=False,
        response_reason=action.response_reason or "Rejected by user",
    )
    repo = PlanRepository(db)
    updated = await repo.get_plan(plan_id, user_id)
    return format_plan_read(updated)


@router.post("/{plan_id}/replan")
async def trigger_replan(
    plan_id: str,
    req: PlanReplanRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PlannerService(db)
    user_id = settings.DEFAULT_USER_ID
    res = await service.trigger_replanning(
        user_id=user_id,
        plan_id=plan_id,
        trigger_reason=req.trigger_reason,
        updated_task_id=req.updated_task_id,
    )
    if res.get("plan_id"):
        repo = PlanRepository(db)
        plan = await repo.get_plan(res["plan_id"], user_id)
        if plan:
            return format_plan_read(plan)
    return res


@router.get("/stream/workflow")
async def stream_planning_progress():
    """
    Server-Sent Events (SSE) streaming progress endpoint for UI workflow visualizations.
    """
    async def event_generator():
        stages = [
            ("parse_goal", "Parsing natural-language goal intent and extracting temporal constraints..."),
            ("load_user_context", "Loading pending tasks, calendar events, and working hour boundaries..."),
            ("decompose_tasks", "Decomposing objectives into atomic actionable tasks and dependency graphs..."),
            ("calculate_utility", "Computing multi-factor mathematical utility scores..."),
            ("generate_schedule", "Running Google OR-Tools CP-SAT deterministic constraint optimizer..."),
            ("validate_constraints", "Verifying zero overlap, working hours, and precedence ordering..."),
            ("present_plan", "Plan formulated and verified. Ready for human review."),
        ]
        for idx, (stage, message) in enumerate(stages):
            data = json.dumps({"step": idx + 1, "total": len(stages), "stage": stage, "message": message})
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
