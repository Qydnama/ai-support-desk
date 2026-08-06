from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.idempotency_records import IdempotencyRecord


async def get_by_key(
    session: AsyncSession,
    *,
    organization_id: UUID,
    key: str,
) -> IdempotencyRecord | None:
    statement = (
        select(IdempotencyRecord)
        .options(joinedload(IdempotencyRecord.message))
        .where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.key == key,
        )
    )

    return await session.scalar(statement)