import time
from datetime import datetime
from typing import Any

from app.integrations.calendar.simulated import simulated_calendar_provider
from app.models.audit import ToolExecutionStatus
from app.models.task import TaskStatus
from app.repositories.calendar_repo import CalendarRepository
from app.repositories.plan_repo import PlanRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.calendar import CalendarEventCreate
from sqlalchemy.ext.asyncio import AsyncSession


class AuraTools:
    """
    Validated tools for task management, calendar operations, and verification.
    All tool invocations record execution logs and enforce permissions and verification.
    """

    def __init__(self, db: AsyncSession, plan_id: str | None = None):
        self.db = db
        self.plan_id = plan_id
        self.task_repo = TaskRepository(db)
        self.cal_repo = CalendarRepository(db)
        self.plan_repo = PlanRepository(db)

    async def list_tasks(self, user_id: str, status: TaskStatus | None = None) -> list[dict[str, Any]]:
        t0 = time.time()
        tasks = await self.task_repo.list_tasks(user_id=user_id, status=status)
        latency = int((time.time() - t0) * 1000)

        data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "estimated_duration_minutes": t.estimated_duration_minutes,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "priority": t.priority,
                "utility_score": t.utility_score,
                "status": t.status.value,
                "mandatory": t.mandatory,
                "dependencies": [d.depends_on_task_id for d in t.dependencies],
            }
            for t in tasks
        ]

        await self.plan_repo.add_tool_log(
            plan_id=self.plan_id,
            tool_name="list_tasks",
            input_payload={"user_id": user_id, "status": status.value if status else None},
            output_payload={"count": len(data)},
            status=ToolExecutionStatus.SUCCESS,
            verified=True,
            latency_ms=latency,
        )
        return data

    async def read_calendar_events(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        t0 = time.time()
        events = await self.cal_repo.list_events(user_id=user_id, start_time=start_time, end_time=end_time)
        latency = int((time.time() - t0) * 1000)

        data = [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "is_fixed": e.is_fixed,
                "source": e.source,
            }
            for e in events
        ]

        await self.plan_repo.add_tool_log(
            plan_id=self.plan_id,
            tool_name="read_calendar_events",
            input_payload={"user_id": user_id, "start_time": start_time.isoformat(), "end_time": end_time.isoformat()},
            output_payload={"count": len(data)},
            status=ToolExecutionStatus.SUCCESS,
            verified=True,
            latency_ms=latency,
        )
        return data

    async def execute_approved_calendar_commit(
        self,
        user_id: str,
        scheduled_slots: list[dict[str, Any]],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Commits scheduled slots to the calendar.
        Requires verified creation through calendar adapter and records audit logs.
        """
        t0 = time.time()
        committed_events = []
        errors = []

        for slot in scheduled_slots:
            try:
                start_dt = (
                    slot["start_time"]
                    if isinstance(slot["start_time"], datetime)
                    else datetime.fromisoformat(slot["start_time"])
                )
                end_dt = (
                    slot["end_time"]
                    if isinstance(slot["end_time"], datetime)
                    else datetime.fromisoformat(slot["end_time"])
                )

                # 1. Call provider
                provider_resp = await simulated_calendar_provider.create_event(
                    user_id=user_id,
                    title=f"AURA: {slot['task_title']}",
                    start_time=start_dt,
                    end_time=end_dt,
                    description=f"Auto-scheduled task (Utility: {slot.get('utility_score', 0):.2f})",
                    idempotency_key=f"{idempotency_key}_{slot['task_id']}" if idempotency_key else None,
                )

                # 2. Independent verification check
                is_verified = await simulated_calendar_provider.verify_event(
                    user_id=user_id,
                    external_event_id=provider_resp["event_id"],
                )

                if not is_verified:
                    errors.append(f"Verification failed for event {provider_resp['event_id']}")
                    continue

                # 3. Save to database calendar events
                db_event = await self.cal_repo.create_event(
                    user_id=user_id,
                    event_in=CalendarEventCreate(
                        title=f"AURA: {slot['task_title']}",
                        description=f"Auto-scheduled task (Task ID: {slot['task_id']})",
                        start_time=start_dt,
                        end_time=end_dt,
                        is_fixed=True,
                        external_event_id=provider_resp["event_id"],
                        source="aura_plan",
                    ),
                )

                # 4. Update task status to SCHEDULED
                await self.task_repo.update_task(
                    task_id=slot["task_id"],
                    user_id=user_id,
                    status=TaskStatus.SCHEDULED,
                )

                committed_events.append({
                    "task_id": slot["task_id"],
                    "calendar_event_id": db_event.id,
                    "external_event_id": provider_resp["event_id"],
                    "verified": True,
                })
            except Exception as e:
                errors.append(f"Failed to commit slot for task {slot.get('task_id')}: {e!s}")

        latency = int((time.time() - t0) * 1000)
        overall_status = ToolExecutionStatus.SUCCESS if not errors else ToolExecutionStatus.FAILED

        await self.plan_repo.add_tool_log(
            plan_id=self.plan_id,
            tool_name="commit_calendar_events",
            input_payload={"user_id": user_id, "slots_count": len(scheduled_slots)},
            output_payload={"committed_count": len(committed_events), "errors": errors},
            status=overall_status,
            verified=len(errors) == 0,
            verification_details={"verified_count": len(committed_events)},
            error_message="; ".join(errors) if errors else None,
            latency_ms=latency,
            idempotency_key=idempotency_key,
        )

        return {
            "success": len(errors) == 0,
            "committed_events": committed_events,
            "errors": errors,
        }
