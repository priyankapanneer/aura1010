import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.agents.optimizer import ScheduleOptimizer
from app.agents.state import AuraState
from app.agents.tools import AuraTools
from app.agents.utility import UtilityCalculator
from app.integrations.llm.factory import get_llm_provider
from app.models.plan import PlanStatus
from app.models.task import TaskStatus
from app.repositories.calendar_repo import CalendarRepository
from app.repositories.plan_repo import PlanRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.schemas.task import TaskCreate
from sqlalchemy.ext.asyncio import AsyncSession


async def parse_goal_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    llm = get_llm_provider()
    current_time_iso = state.get("current_time_iso", datetime.now(UTC).isoformat())

    user_context = state.get("user_context", {})
    output = await llm.parse_and_decompose_goal(
        goal_prompt=state["goal_prompt"],
        current_time_iso=current_time_iso,
        user_context=user_context,
    )

    if output.is_ambiguous:
        return {
            "is_ambiguous": True,
            "clarification_question": output.clarification_question,
            "explanation": output.explanation,
        }

    raw_tasks = [t.model_dump() for t in output.extracted_tasks]
    return {
        "is_ambiguous": False,
        "candidate_tasks": raw_tasks,
        "conflicts": [],
    }


async def load_user_context_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    user_id = state["user_id"]
    user_repo = UserRepository(db)
    task_repo = TaskRepository(db)
    cal_repo = CalendarRepository(db)

    user_settings = await user_repo.get_user_settings(user_id)
    settings_dict = {
        "work_start_time": user_settings.work_start_time if user_settings else "09:00",
        "work_end_time": user_settings.work_end_time if user_settings else "18:00",
        "utility_weights": user_settings.utility_weights if user_settings else {
            "urgency": 0.35, "importance": 0.25, "impact": 0.15, "dependency": 0.15, "efficiency": 0.10
        },
    }

    # Load existing pending tasks
    pending_tasks = await task_repo.list_tasks(user_id=user_id, status=TaskStatus.PENDING)
    pending_list = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "estimated_duration_minutes": t.estimated_duration_minutes,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "priority": t.priority,
            "mandatory": t.mandatory,
            "dependencies": [d.depends_on_task_id for d in t.dependencies],
        }
        for t in pending_tasks
    ]

    # Load today's calendar events
    now = datetime.fromisoformat(state.get("current_time_iso", datetime.now(UTC).isoformat()))
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

    events = await cal_repo.list_events(user_id=user_id, start_time=day_start, end_time=day_end)
    events_list = [
        {
            "id": e.id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "is_fixed": e.is_fixed,
        }
        for e in events
    ]

    return {
        "user_context": {
            "settings": settings_dict,
            "pending_tasks": pending_list,
            "calendar_events": events_list,
        }
    }


async def decompose_tasks_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    user_id = state["user_id"]
    task_repo = TaskRepository(db)

    extracted = state.get("candidate_tasks", [])
    candidate_tasks = []
    dep_graph: dict[str, list[str]] = {}

    # Persistent creation of new decomposed tasks if they don't have a database ID
    for item in extracted:
        item_id = item.get("id")
        # Check if already exists in DB
        existing = await task_repo.get_task(item_id, user_id) if item_id else None
        if not existing:
            # Create in database so it has permanent persistence
            deadline_val = item.get("deadline")
            deadline_dt = datetime.fromisoformat(deadline_val) if isinstance(deadline_val, str) else deadline_val
            created = await task_repo.create_task(
                user_id=user_id,
                task_in=TaskCreate(
                    title=item["title"],
                    description=item.get("description"),
                    estimated_duration_minutes=item.get("estimated_duration_minutes", 30),
                    deadline=deadline_dt,
                    priority=item.get("priority", 3),
                    mandatory=item.get("mandatory", False),
                    source="agent_decomposed",
                    confidence=item.get("confidence", 0.95),
                    dependencies=item.get("dependencies", []),
                ),
            )
            item["id"] = created.id
        candidate_tasks.append(item)
        dep_graph[item["id"]] = item.get("dependencies", [])

    return {
        "candidate_tasks": candidate_tasks,
        "dependency_graph": dep_graph,
    }


async def calculate_utility_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    user_context = state.get("user_context", {})
    weights = user_context.get("settings", {}).get("utility_weights")
    calculator = UtilityCalculator(weights=weights)

    now = datetime.fromisoformat(state.get("current_time_iso", datetime.now(UTC).isoformat()))
    tasks = state.get("candidate_tasks", [])
    dep_graph = state.get("dependency_graph", {})

    scored_tasks = []
    breakdowns = []

    for t in tasks:
        breakdown = calculator.calculate_task_utility(
            task=t,
            current_time=now,
            dependency_graph=dep_graph,
            total_tasks_count=len(tasks),
        )
        t_copy = dict(t)
        t_copy["utility_score"] = breakdown.total_utility
        scored_tasks.append(t_copy)
        breakdowns.append(breakdown.model_dump())

    return {
        "candidate_tasks": scored_tasks,
        "utility_scores": breakdowns,
    }


async def generate_schedule_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    optimizer = ScheduleOptimizer(buffer_minutes_between_tasks=5)
    user_context = state.get("user_context", {})
    settings = user_context.get("settings", {})

    now = datetime.fromisoformat(state.get("current_time_iso", datetime.now(UTC).isoformat()))
    # Working window from user settings (e.g. 09:00 to 18:00)
    w_start_str = settings.get("work_start_time", "09:00")
    w_end_str = settings.get("work_end_time", "18:00")

    sh, sm = map(int, w_start_str.split(":"))
    eh, em = map(int, w_end_str.split(":"))

    window_start = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    if window_start < now:
        # If current time is already inside working window, start from current time
        window_start = now
    window_end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
    if window_end <= window_start:
        window_end = window_start + timedelta(hours=8)

    # Fixed events from user_context
    raw_events = user_context.get("calendar_events", [])
    fixed_events = []
    for ev in raw_events:
        fixed_events.append({
            "id": ev["id"],
            "title": ev["title"],
            "start_time": datetime.fromisoformat(ev["start_time"]),
            "end_time": datetime.fromisoformat(ev["end_time"]),
        })

    tasks = state.get("candidate_tasks", [])
    opt_result = optimizer.optimize_schedule(
        tasks=tasks,
        fixed_events=fixed_events,
        window_start=window_start,
        window_end=window_end,
    )

    return {
        "scheduled_slots": [s.model_dump() for s in opt_result.scheduled_slots],
        "unscheduled_items": [u.model_dump() for u in opt_result.unscheduled_items],
        "conflicts": opt_result.conflicts,
        "objective_value": opt_result.objective_value,
    }


async def validate_constraints_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    unscheduled = state.get("unscheduled_items", [])
    hard_conflicts = [u for u in unscheduled if u.get("hard_conflict")]

    conflicts = list(state.get("conflicts", []))
    if hard_conflicts:
        for hc in hard_conflicts:
            conflicts.append(f"Hard constraint conflict: '{hc.get('task_title')}' - {hc.get('reason')}")

    return {"conflicts": list(set(conflicts))}


async def present_plan_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    llm = get_llm_provider()
    user_id = state["user_id"]
    plan_repo = PlanRepository(db)

    scheduled = state.get("scheduled_slots", [])
    unscheduled = state.get("unscheduled_items", [])
    conflicts = state.get("conflicts", [])

    explanation = await llm.generate_explanation(
        scheduled_tasks=scheduled,
        unscheduled_tasks=unscheduled,
        conflicts=conflicts,
    )

    # Save plan to database
    plan = await plan_repo.create_plan(
        user_id=user_id,
        goal_prompt=state["goal_prompt"],
        version=1,
        explanation=explanation,
        objective_score=state.get("objective_value", 0.0),
        metadata_json={
            "scheduled_count": len(scheduled),
            "unscheduled_count": len(unscheduled),
            "conflicts": conflicts,
        },
    )

    # Add plan items
    plan_items = []
    for slot in scheduled:
        plan_items.append({
            "task_id": slot["task_id"],
            "scheduled_start": slot["start_time"],
            "scheduled_end": slot["end_time"],
            "order_index": slot["order_index"],
            "is_scheduled": True,
            "utility_score": slot["utility_score"],
            "status": "PROPOSED",
        })

    for item in unscheduled:
        plan_items.append({
            "task_id": item["task_id"],
            "order_index": 999,
            "is_scheduled": False,
            "unscheduled_reason": item["reason"],
            "utility_score": 0.0,
            "status": "UNSCHEDULED",
        })

    await plan_repo.add_plan_items(plan.id, plan_items)
    await plan_repo.update_plan_status(plan.id, user_id, PlanStatus.PROPOSED)

    return {
        "plan_id": plan.id,
        "explanation": explanation,
        "requires_approval": True,
        "approval_status": "PENDING",
    }


async def request_approval_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    plan_id = state.get("plan_id")
    user_id = state["user_id"]
    plan_repo = PlanRepository(db)

    if plan_id:
        await plan_repo.create_approval_request(
            plan_id=plan_id,
            user_id=user_id,
            action_type="CALENDAR_WRITE",
            payload={
                "scheduled_slots_count": len(state.get("scheduled_slots", [])),
                "tasks": [s.get("task_title") for s in state.get("scheduled_slots", [])],
            },
        )

    return {"approval_status": "PENDING"}


async def execute_approved_actions_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    plan_id = state.get("plan_id")
    user_id = state["user_id"]
    tools = AuraTools(db, plan_id=plan_id)

    scheduled = state.get("scheduled_slots", [])
    idempotency_key = f"exec_{plan_id or uuid.uuid4().hex}"

    exec_result = await tools.execute_approved_calendar_commit(
        user_id=user_id,
        scheduled_slots=scheduled,
        idempotency_key=idempotency_key,
    )

    return {
        "execution_results": exec_result.get("committed_events", []),
        "all_executions_verified": exec_result.get("success", False),
        "execution_errors": exec_result.get("errors", []),
    }


async def verify_execution_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    plan_id = state.get("plan_id")
    user_id = state["user_id"]
    plan_repo = PlanRepository(db)

    all_verified = state.get("all_executions_verified", False)
    if all_verified and plan_id:
        await plan_repo.update_plan_status(plan_id, user_id, PlanStatus.EXECUTED)

    return {"all_executions_verified": all_verified}


async def handle_rejection_node(state: AuraState, db: AsyncSession) -> dict[str, Any]:
    plan_id = state.get("plan_id")
    user_id = state["user_id"]
    plan_repo = PlanRepository(db)

    if plan_id:
        await plan_repo.update_plan_status(
            plan_id=plan_id,
            user_id=user_id,
            status=PlanStatus.REJECTED,
            explanation=f"User rejected plan: {state.get('approval_response_reason', 'No reason provided')}",
        )

    return {"approval_status": "REJECTED"}
