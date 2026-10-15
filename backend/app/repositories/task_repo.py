
from app.models.task import Task, TaskDependency, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tasks(
        self,
        user_id: str,
        status: TaskStatus | None = None,
        mandatory: bool | None = None,
    ) -> list[Task]:
        query = (
            select(Task)
            .where(Task.user_id == user_id)
            .options(selectinload(Task.dependencies))
            .order_by(Task.utility_score.desc(), Task.created_at.desc())
        )
        if status:
            query = query.where(Task.status == status)
        if mandatory is not None:
            query = query.where(Task.mandatory == mandatory)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task(self, task_id: str, user_id: str) -> Task | None:
        query = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(selectinload(Task.dependencies), selectinload(Task.dependents))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_task(self, user_id: str, task_in: TaskCreate) -> Task:
        task = Task(
            user_id=user_id,
            title=task_in.title,
            description=task_in.description,
            estimated_duration_minutes=task_in.estimated_duration_minutes,
            deadline=task_in.deadline,
            priority=task_in.priority,
            mandatory=task_in.mandatory,
            source=task_in.source,
            confidence=task_in.confidence,
            status=TaskStatus.PENDING,
        )
        self.db.add(task)
        await self.db.flush()

        if task_in.dependencies:
            for dep_id in task_in.dependencies:
                dep = TaskDependency(task_id=task.id, depends_on_task_id=dep_id)
                self.db.add(dep)
            await self.db.flush()

        await self.db.commit()
        return await self.get_task(task.id, user_id)

    async def update_task(self, task_id: str, user_id: str, updates: TaskUpdate | None = None, status: TaskStatus | None = None) -> Task | None:
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        if status is not None:
            task.status = status

        if updates is not None:
            update_dict = updates.model_dump(exclude_unset=True)
            deps = update_dict.pop("dependencies", None)

            for key, value in update_dict.items():
                setattr(task, key, value)

            if deps is not None:
                # Delete existing dependencies
                existing_deps = await self.db.execute(
                    select(TaskDependency).where(TaskDependency.task_id == task_id)
                )
                for old_dep in existing_deps.scalars().all():
                    await self.db.delete(old_dep)
                await self.db.flush()

                # Add new dependencies
                for dep_id in deps:
                    new_dep = TaskDependency(task_id=task.id, depends_on_task_id=dep_id)
                    self.db.add(new_dep)
                await self.db.flush()

        await self.db.commit()
        return await self.get_task(task.id, user_id)

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        task = await self.get_task(task_id, user_id)
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True
