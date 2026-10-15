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
async def test_adaptive_replanning_creates_versioned_diff(async_db: AsyncSession):
    planner = PlannerService(async_db)
    user_id = settings.DEFAULT_USER_ID

    # 1. Initial Plan
    initial = await planner.generate_plan(
        user_id=user_id,
        goal_prompt="Plan today's urgent milestones.",
        auto_approve_simulated=False,
    )
    initial_plan_id = initial["plan_id"]

    # 2. Trigger Replanning (e.g., Task ran 60 minutes over)
    replanned = await planner.trigger_replanning(
        user_id=user_id,
        plan_id=initial_plan_id,
        trigger_reason="DURATION_EXCEEDED_BY_60_MIN",
    )

    new_plan_id = replanned["plan_id"]
    assert new_plan_id != initial_plan_id

    plan_repo = PlanRepository(async_db)
    old_p = await plan_repo.get_plan(initial_plan_id, user_id)
    new_p = await plan_repo.get_plan(new_plan_id, user_id)

    # Old plan transitioned to REPLANNED
    assert old_p.status.value == "REPLANNED"
    # New plan version incremented
    assert new_p.version == 2
    assert new_p.parent_plan_id == initial_plan_id

    # Audit diff recorded
    assert len(new_p.replanning_audits) == 1
    audit = new_p.replanning_audits[0]
    assert audit.trigger_reason == "DURATION_EXCEEDED_BY_60_MIN"
    assert "Version 1" in audit.before_summary
    assert "Version 2" in audit.after_summary
