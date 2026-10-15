import logging
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, async_engine
from app.models.calendar import CalendarEvent
from app.models.task import Task, TaskDependency, TaskPriority, TaskStatus
from app.repositories.user_repo import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


async def init_db():
    """Initializes tables and seeds initial demo data if configured."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.AUTO_SEED:
        async with AsyncSessionLocal() as session:
            await seed_demo_data(session)


async def seed_demo_data(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_or_create_default_user()

    # Check if tasks already exist
    existing_tasks = await session.execute(select(Task).where(Task.user_id == user.id))
    if existing_tasks.scalars().first():
        logger.info("Demo database already seeded.")
        return

    logger.info("Seeding realistic demo tasks and calendar fixtures...")
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    today_9am = now.replace(hour=9)

    # 1. Calendar Events (Fixed meetings)
    events = [
        CalendarEvent(
            user_id=user.id,
            title="Team Architecture Sync",
            description="Weekly engineering synchronization meeting",
            start_time=today_9am + timedelta(hours=1),   # 10:00 - 11:00
            end_time=today_9am + timedelta(hours=2),
            is_fixed=True,
            source="calendar_fixture",
        ),
        CalendarEvent(
            user_id=user.id,
            title="Stakeholder Sprint Review",
            description="Review sprint deliverables and milestones",
            start_time=today_9am + timedelta(hours=4),   # 13:00 - 14:00
            end_time=today_9am + timedelta(hours=5),
            is_fixed=True,
            source="calendar_fixture",
        ),
    ]
    for ev in events:
        session.add(ev)

    # 2. Existing Pending Tasks
    t1 = Task(
        user_id=user.id,
        title="Complete Critical Client Deliverable",
        description="Finalize performance audit report before 5 PM deadline",
        estimated_duration_minutes=90,
        deadline=today_9am + timedelta(hours=8),  # 17:00
        priority=TaskPriority.URGENT.value,
        mandatory=True,
        status=TaskStatus.PENDING,
        source="user",
        utility_score=1.85,
    )
    t2 = Task(
        user_id=user.id,
        title="Review PR: OAuth Security Patch",
        description="Peer-review multi-tenant security verification code",
        estimated_duration_minutes=45,
        deadline=today_9am + timedelta(hours=7),  # 16:00
        priority=TaskPriority.HIGH.value,
        mandatory=False,
        status=TaskStatus.PENDING,
        source="user",
        utility_score=1.20,
    )
    t3 = Task(
        user_id=user.id,
        title="Refactor Database Indexes",
        description="Add composite index on plan_items for fast query lookups",
        estimated_duration_minutes=60,
        deadline=today_9am + timedelta(hours=9),  # 18:00
        priority=TaskPriority.MEDIUM.value,
        mandatory=False,
        status=TaskStatus.PENDING,
        source="user",
        utility_score=0.75,
    )

    session.add_all([t1, t2, t3])
    await session.flush()

    # Add dependency: t2 depends on t1
    dep = TaskDependency(task_id=t2.id, depends_on_task_id=t1.id)
    session.add(dep)

    await session.commit()
    logger.info("Demo data seeding completed successfully.")
