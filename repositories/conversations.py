from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import ConversationStatus
from models.conversations import Conversation


async def get_by_id(
    session: AsyncSession,
    conversation_id: UUID,
) -> Conversation | None:
    return await session.get(
        Conversation,
        conversation_id,
    )


async def list_by_organization(
    session: AsyncSession,
    *,
    organization_id: UUID,
    status: ConversationStatus | None,
    limit: int,
    offset: int,
) -> list[Conversation]:
    statement = select(Conversation).where(
        Conversation.organization_id == organization_id,
    )

    if status is not None:
        statement = statement.where(
            Conversation.status == status,
        )

    statement = (
        statement
        .order_by(
            Conversation.created_at,
            Conversation.id,
        )
        .offset(offset)
        .limit(limit)
    )

    conversations = await session.scalars(statement)

    return list(conversations)
