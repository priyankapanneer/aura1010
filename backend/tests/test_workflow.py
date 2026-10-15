
import pytest
from app.agents.planner import PlannerService
from app.core.config import settings
from app.core.database import Base
from app.db.init_db import seed_demo_data
from app.repositories.plan_repo import PlanRepository
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        await seed_demo_data(session)
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_full_planning_workflow_interrupt_and_approval(async_db: AsyncSession):
    planner = PlannerService(async_db)
    user_id = settings.DEFAULT_USER_ID

    # 1. User submits natural-language goal
    prompt = "Plan my day. I have a project deadline at 5 PM, two meetings, three pending tasks, and I need one hour to study."
    result = await planner.generate_plan(user_id=user_id, goal_prompt=prompt, auto_approve_simulated=False)

    assert result["plan_id"] is not None
    assert result["status"] == "PROPOSED"
    assert len(result["scheduled_slots"]) > 0
    assert result["is_ambiguous"] is False

    plan_id = result["plan_id"]

    # 2. Inspect plan state before approval (should not have executed calendar commits)
    plan_repo = PlanRepository(async_db)
    plan = await plan_repo.get_plan(plan_id, user_id)
    assert plan.status.value == "PROPOSED"
    assert len(plan.approval_requests) == 1
    assert plan.approval_requests[0].status.value == "PENDING"

    # 3. User Approves Plan
    approval_result = await planner.handle_approval_decision(
        user_id=user_id,
        plan_id=plan_id,
        approved=True,
        response_reason="Approved after inspection",
    )

    assert approval_result["approved"] is True
    assert approval_result["verified"] is True
    assert approval_result["status"] == "EXECUTED"
    assert len(approval_result["execution_results"]) > 0


@pytest.mark.asyncio
async def test_planning_workflow_rejection(async_db: AsyncSession):
    planner = PlannerService(async_db)
    user_id = settings.DEFAULT_USER_ID

    prompt = "Plan my day with 2 hours of study."
    result = await planner.generate_plan(user_id=user_id, goal_prompt=prompt, auto_approve_simulated=False)
    plan_id = result["plan_id"]

    # User Rejects Plan
    rejection_result = await planner.handle_approval_decision(
        user_id=user_id,
        plan_id=plan_id,
        approved=False,
        response_reason="Timing conflicts with personal event",
    )

    assert rejection_result["approved"] is False
    assert rejection_result["status"] == "REJECTED"
    assert len(rejection_result["execution_results"]) == 0
