import uuid
from datetime import UTC, datetime
from typing import Any

from app.agents.graph import build_aura_graph
from app.agents.state import AuraState
from app.models.plan import ApprovalStatus, PlanStatus
from app.repositories.calendar_repo import CalendarRepository
from app.repositories.plan_repo import PlanRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class PlannerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_repo = PlanRepository(db)
        self.task_repo = TaskRepository(db)
        self.cal_repo = CalendarRepository(db)
        self.user_repo = UserRepository(db)

    async def generate_plan(
        self,
        user_id: str,
        goal_prompt: str,
        auto_approve_simulated: bool = False,
    ) -> dict[str, Any]:
        """
        Runs the full LangGraph planning pipeline.
        Stops at 'request_approval' unless auto_approve_simulated is requested.
        """
        now_iso = datetime.now(UTC).isoformat()
        thread_id = f"plan_thread_{uuid.uuid4().hex[:12]}"

        graph = build_aura_graph(self.db)

        initial_state: AuraState = {
            "user_id": user_id,
            "goal_prompt": goal_prompt,
            "current_time_iso": now_iso,
            "approval_status": "PENDING",
            "execution_results": [],
            "conflicts": [],
        }

        config = {"configurable": {"thread_id": thread_id}}
        result_state = await graph.ainvoke(initial_state, config=config)

        plan_id = result_state.get("plan_id")

        if auto_approve_simulated and plan_id:
            # Resume graph with approval
            resumed_state = await self.handle_approval_decision(
                user_id=user_id,
                plan_id=plan_id,
                approved=True,
                response_reason="Auto-approved in simulation mode",
            )
            return resumed_state

        plan_record = await self.plan_repo.get_plan(plan_id, user_id) if plan_id else None
        return {
            "plan_id": plan_id,
            "status": plan_record.status.value if plan_record else "DRAFT",
            "is_ambiguous": result_state.get("is_ambiguous", False),
            "clarification_question": result_state.get("clarification_question"),
            "explanation": result_state.get("explanation"),
            "scheduled_slots": result_state.get("scheduled_slots", []),
            "unscheduled_items": result_state.get("unscheduled_items", []),
            "conflicts": result_state.get("conflicts", []),
            "objective_value": result_state.get("objective_value", 0.0),
            "thread_id": thread_id,
        }

    async def handle_approval_decision(
        self,
        user_id: str,
        plan_id: str,
        approved: bool,
        response_reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Resumes the workflow after human approval or rejection.
        """
        plan = await self.plan_repo.get_plan(plan_id, user_id)
        if not plan:
            raise ValueError(f"Plan with id {plan_id} not found")

        # Update approval request record in database
        for req in plan.approval_requests:
            if req.status == ApprovalStatus.PENDING:
                await self.plan_repo.update_approval_request(
                    request_id=req.id,
                    user_id=user_id,
                    status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
                    reason=response_reason,
                )

        scheduled_slots = []
        for item in plan.items:
            if item.is_scheduled and item.scheduled_start and item.scheduled_end:
                scheduled_slots.append({
                    "task_id": item.task_id,
                    "task_title": item.task.title if item.task else "Task",
                    "start_time": item.scheduled_start,
                    "end_time": item.scheduled_end,
                    "utility_score": item.utility_score,
                })

        # Run execution or rejection node
        state_update: AuraState = {
            "user_id": user_id,
            "plan_id": plan_id,
            "goal_prompt": plan.goal_prompt,
            "approval_status": "APPROVED" if approved else "REJECTED",
            "approval_response_reason": response_reason,
            "scheduled_slots": scheduled_slots,
            "current_time_iso": datetime.now(UTC).isoformat(),
        }

        if approved:
            # Execute and verify
            from app.agents.nodes import execute_approved_actions_node, verify_execution_node
            exec_res = await execute_approved_actions_node(state_update, self.db)
            state_update.update(exec_res)
            verify_res = await verify_execution_node(state_update, self.db)
            state_update.update(verify_res)
        else:
            from app.agents.nodes import handle_rejection_node
            await handle_rejection_node(state_update, self.db)

        # Refresh plan
        updated_plan = await self.plan_repo.get_plan(plan_id, user_id)
        return {
            "plan_id": plan_id,
            "status": updated_plan.status.value,
            "approved": approved,
            "verified": state_update.get("all_executions_verified", False),
            "execution_results": state_update.get("execution_results", []),
            "execution_errors": state_update.get("execution_errors", []),
        }

    async def trigger_replanning(
        self,
        user_id: str,
        plan_id: str,
        trigger_reason: str,
        updated_task_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Adaptive replanning:
        Reads current persisted state, identifies affected constraints,
        preserves completed work, re-runs constraint optimizer,
        records before-and-after audit diff, and presents revised plan.
        """
        old_plan = await self.plan_repo.get_plan(plan_id, user_id)
        if not old_plan:
            raise ValueError(f"Plan {plan_id} not found for replanning")

        # Mark old plan as REPLANNED
        await self.plan_repo.update_plan_status(old_plan.id, user_id, PlanStatus.REPLANNED)

        # Summarize before state
        before_slots = [
            f"{it.task.title if it.task else it.task_id} ({it.scheduled_start.strftime('%H:%M')}-{it.scheduled_end.strftime('%H:%M')})"
            for it in old_plan.items if it.is_scheduled and it.scheduled_start and it.scheduled_end
        ]
        before_summary = f"Version {old_plan.version}: " + (", ".join(before_slots) if before_slots else "No scheduled slots")

        # Generate revised plan (new version)
        revised_res = await self.generate_plan(
            user_id=user_id,
            goal_prompt=f"[Replanned: {trigger_reason}] {old_plan.goal_prompt}",
            auto_approve_simulated=False,
        )

        new_plan_id = revised_res["plan_id"]
        if new_plan_id:
            new_plan = await self.plan_repo.get_plan(new_plan_id, user_id)
            new_plan.version = old_plan.version + 1
            new_plan.parent_plan_id = old_plan.id
            await self.db.commit()

            after_slots = [
                f"{it.task.title if it.task else it.task_id} ({it.scheduled_start.strftime('%H:%M')}-{it.scheduled_end.strftime('%H:%M')})"
                for it in new_plan.items if it.is_scheduled and it.scheduled_start and it.scheduled_end
            ]
            after_summary = f"Version {new_plan.version}: " + (", ".join(after_slots) if after_slots else "No scheduled slots")

            # Record audit diff
            await self.plan_repo.add_replanning_audit(
                plan_id=new_plan_id,
                trigger_reason=trigger_reason,
                before_summary=before_summary,
                after_summary=after_summary,
                changes={
                    "old_plan_id": old_plan.id,
                    "new_plan_id": new_plan_id,
                    "trigger_reason": trigger_reason,
                    "updated_task_id": updated_task_id,
                },
            )

        return revised_res
