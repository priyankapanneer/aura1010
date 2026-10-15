
from app.core.config import settings
from app.core.database import get_db
from app.models.task import TaskStatus
from app.repositories.task_repo import TaskRepository
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    status: TaskStatus | None = None,
    mandatory: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    user_id = settings.DEFAULT_USER_ID
    tasks = await repo.list_tasks(user_id=user_id, status=status, mandatory=mandatory)

    results = []
    for t in tasks:
        deps = [d.depends_on_task_id for d in t.dependencies]
        t_dict = {
            "id": t.id,
            "user_id": t.user_id,
            "title": t.title,
            "description": t.description,
            "estimated_duration_minutes": t.estimated_duration_minutes,
            "deadline": t.deadline,
            "priority": t.priority,
            "utility_score": t.utility_score,
            "status": t.status,
            "mandatory": t.mandatory,
            "source": t.source,
            "confidence": t.confidence,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "dependencies": deps,
        }
        results.append(TaskRead(**t_dict))
    return results


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    user_id = settings.DEFAULT_USER_ID
    task = await repo.create_task(user_id=user_id, task_in=task_in)
    deps = [d.depends_on_task_id for d in task.dependencies]
    return TaskRead(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        estimated_duration_minutes=task.estimated_duration_minutes,
        deadline=task.deadline,
        priority=task.priority,
        utility_score=task.utility_score,
        status=task.status,
        mandatory=task.mandatory,
        source=task.source,
        confidence=task.confidence,
        created_at=task.created_at,
        updated_at=task.updated_at,
        dependencies=deps,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    user_id = settings.DEFAULT_USER_ID
    task = await repo.get_task(task_id=task_id, user_id=user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    deps = [d.depends_on_task_id for d in task.dependencies]
    return TaskRead(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        estimated_duration_minutes=task.estimated_duration_minutes,
        deadline=task.deadline,
        priority=task.priority,
        utility_score=task.utility_score,
        status=task.status,
        mandatory=task.mandatory,
        source=task.source,
        confidence=task.confidence,
        created_at=task.created_at,
        updated_at=task.updated_at,
        dependencies=deps,
    )


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    user_id = settings.DEFAULT_USER_ID
    task = await repo.update_task(task_id=task_id, user_id=user_id, updates=updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    deps = [d.depends_on_task_id for d in task.dependencies]
    return TaskRead(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        estimated_duration_minutes=task.estimated_duration_minutes,
        deadline=task.deadline,
        priority=task.priority,
        utility_score=task.utility_score,
        status=task.status,
        mandatory=task.mandatory,
        source=task.source,
        confidence=task.confidence,
        created_at=task.created_at,
        updated_at=task.updated_at,
        dependencies=deps,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    user_id = settings.DEFAULT_USER_ID
    deleted = await repo.delete_task(task_id=task_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
