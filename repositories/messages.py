from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.messages import Message


async def list_by_conversation(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    limit: int,
    offset: int,
) -> list[Message]:
    statement = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
        )
        .order_by(
            Message.created_at,
            Message.id,
        )
        .offset(offset)
        .limit(limit)
    )

    messages = await session.scalars(statement)

    return list(messages)
