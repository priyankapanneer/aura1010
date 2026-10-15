from datetime import UTC, datetime
from typing import Any

from app.models.audit import ReplanningAudit, ToolExecutionLog, ToolExecutionStatus
from app.models.plan import ApprovalRequest, ApprovalStatus, Plan, PlanItem, PlanStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(
        self,
        user_id: str,
        goal_prompt: str,
        version: int = 1,
        parent_plan_id: str | None = None,
        explanation: str | None = None,
        objective_score: float = 0.0,
        metadata_json: dict[str, Any] | None = None,
    ) -> Plan:
        plan = Plan(
            user_id=user_id,
            goal_prompt=goal_prompt,
            status=PlanStatus.DRAFT,
            version=version,
            parent_plan_id=parent_plan_id,
            explanation=explanation,
            objective_score=objective_score,
            metadata_json=metadata_json or {},
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def get_plan(self, plan_id: str, user_id: str) -> Plan | None:
        query = (
            select(Plan)
            .where(Plan.id == plan_id, Plan.user_id == user_id)
            .options(
                selectinload(Plan.items).selectinload(PlanItem.task),
                selectinload(Plan.approval_requests),
                selectinload(Plan.tool_logs),
                selectinload(Plan.replanning_audits),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_plans(self, user_id: str, limit: int = 20) -> list[Plan]:
        query = (
            select(Plan)
            .where(Plan.user_id == user_id)
            .options(
                selectinload(Plan.items).selectinload(PlanItem.task),
                selectinload(Plan.approval_requests),
                selectinload(Plan.replanning_audits),
            )
            .order_by(Plan.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_plan_status(
        self,
        plan_id: str,
        user_id: str,
        status: PlanStatus,
        explanation: str | None = None,
        objective_score: float | None = None,
    ) -> Plan | None:
        plan = await self.get_plan(plan_id, user_id)
        if not plan:
            return None
        plan.status = status
        if explanation is not None:
            plan.explanation = explanation
        if objective_score is not None:
            plan.objective_score = objective_score
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def add_plan_items(self, plan_id: str, items: list[dict[str, Any]]) -> list[PlanItem]:
        plan_items = []
        for it in items:
            p_item = PlanItem(
                plan_id=plan_id,
                task_id=it["task_id"],
                scheduled_start=it.get("scheduled_start"),
                scheduled_end=it.get("scheduled_end"),
                order_index=it.get("order_index", 0),
                is_scheduled=it.get("is_scheduled", True),
                unscheduled_reason=it.get("unscheduled_reason"),
                utility_score=it.get("utility_score", 0.0),
                status=it.get("status", "SCHEDULED"),
            )
            self.db.add(p_item)
            plan_items.append(p_item)
        await self.db.commit()
        return plan_items

    async def create_approval_request(
        self,
        plan_id: str,
        user_id: str,
        action_type: str,
        payload: dict[str, Any],
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            plan_id=plan_id,
            user_id=user_id,
            action_type=action_type,
            payload=payload,
            status=ApprovalStatus.PENDING,
        )
        self.db.add(req)
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def update_approval_request(
        self,
        request_id: str,
        user_id: str,
        status: ApprovalStatus,
        reason: str | None = None,
    ) -> ApprovalRequest | None:
        query = select(ApprovalRequest).where(ApprovalRequest.id == request_id, ApprovalRequest.user_id == user_id)
        res = await self.db.execute(query)
        req = res.scalars().first()
        if not req:
            return None
        req.status = status
        req.response_reason = reason
        req.resolved_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def add_tool_log(
        self,
        plan_id: str | None,
        tool_name: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any] | None,
        status: ToolExecutionStatus,
        verified: bool,
        verification_details: dict[str, Any] | None = None,
        error_message: str | None = None,
        latency_ms: int = 0,
        idempotency_key: str | None = None,
    ) -> ToolExecutionLog:
        log = ToolExecutionLog(
            plan_id=plan_id,
            tool_name=tool_name,
            input_payload=input_payload,
            output_payload=output_payload,
            status=status,
            verified=verified,
            verification_details=verification_details,
            error_message=error_message,
            latency_ms=latency_ms,
            idempotency_key=idempotency_key,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def add_replanning_audit(
        self,
        plan_id: str,
        trigger_reason: str,
        before_summary: str,
        after_summary: str,
        changes: dict[str, Any],
    ) -> ReplanningAudit:
        audit = ReplanningAudit(
            plan_id=plan_id,
            trigger_reason=trigger_reason,
            before_summary=before_summary,
            after_summary=after_summary,
            changes=changes,
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit
