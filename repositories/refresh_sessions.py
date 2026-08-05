from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.refresh_sessions import RefreshSession


async def get_by_id_for_update(
    session: AsyncSession,
    session_id: UUID,
) -> RefreshSession | None:
    statement = (
        select(RefreshSession)
        .where(
            RefreshSession.id == session_id,
        )
        .with_for_update()
    )

    return await session.scalar(statement)