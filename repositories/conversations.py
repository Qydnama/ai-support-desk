from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import ConversationStatus
from models.conversations import Conversation
from models.organization_members import OrganizationMember


async def get_by_id_for_user(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    user_id: UUID,
) -> Conversation | None:
    statement = (
        select(Conversation)
        .join(
            OrganizationMember,
            OrganizationMember.organization_id
            == Conversation.organization_id,
        )
        .where(
            Conversation.id == conversation_id,
            OrganizationMember.user_id == user_id,
        )
    )

    return await session.scalar(statement)


async def list_by_organization(
    session: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    status: ConversationStatus | None,
    limit: int,
    offset: int,
) -> list[Conversation]:
    statement = (
        select(Conversation)
        .join(
            OrganizationMember,
            OrganizationMember.organization_id
            == Conversation.organization_id,
        )
        .where(
            Conversation.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
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
