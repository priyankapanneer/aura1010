from app.core.database import get_db
from app.models.audit import ReplanningAudit, ToolExecutionLog
from app.schemas.plan import ReplanningAuditRead, ToolExecutionLogRead
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/audits", response_model=list[ReplanningAuditRead])
async def list_replanning_audits(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(ReplanningAudit).order_by(ReplanningAudit.created_at.desc()).limit(limit)
    res = await db.execute(query)
    audits = res.scalars().all()
    return audits


@router.get("/tools", response_model=list[ToolExecutionLogRead])
async def list_tool_execution_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(ToolExecutionLog).order_by(ToolExecutionLog.created_at.desc()).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()
    return logs
