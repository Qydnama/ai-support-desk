from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.outbox_messages import OutboxMessage


async def list_pending_for_publish(
    session: AsyncSession,
    *,
    limit: int,
) -> list[OutboxMessage]:
    statement = (
        select(OutboxMessage)
        .where(
            OutboxMessage.published_at.is_(None),
        )
        .order_by(
            OutboxMessage.created_at,
            OutboxMessage.id,
        )
        .with_for_update(skip_locked=True)
        .limit(limit)
    )

    messages = await session.scalars(statement)

    return list(messages)
