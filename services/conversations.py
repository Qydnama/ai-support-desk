from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    ContactNotFoundError,
    ConversationAlreadyAssignedError,
    ConversationVersionConflictError,
    OrganizationNotFoundError,
)
from models.conversations import Conversation
from models.users import User
from repositories import contacts as contact_repository
from repositories import conversations as conversation_repository
from repositories import organizations as organization_repository
from schemas.conversations import (
    ConversationCreate,
    ConversationUpdate,
)

async def create_conversation(
    session: AsyncSession,
    data: ConversationCreate,
) -> Conversation:
    organization = await organization_repository.get_by_id(
        session=session,
        organization_id=data.organization_id,
    )

    if organization is None:
        raise OrganizationNotFoundError()

    contact = await contact_repository.get_active_by_id(
        session=session,
        contact_id=data.contact_id,
        organization_id=data.organization_id,
    )

    if contact is None:
        raise ContactNotFoundError()

    conversation = Conversation(
        id=uuid4(),
        organization_id=data.organization_id,
        contact_id=contact.id,
        subject=data.subject,
    )

    session.add(conversation)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return conversation


async def update_conversation(
    session: AsyncSession,
    conversation: Conversation,
    data: ConversationUpdate,
) -> Conversation:
    try:
        updated_conversation = (
            await conversation_repository.update_status_if_version(
                session=session,
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                status=data.status,
                expected_version=data.expected_version,
            )
        )

        if updated_conversation is None:
            raise ConversationVersionConflictError()

        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return updated_conversation


async def claim_conversation(
    session: AsyncSession,
    conversation: Conversation,
    current_user: User,
) -> Conversation:
    try:
        claimed_conversation = (
            await conversation_repository.claim_if_unassigned(
                session=session,
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                user_id=current_user.id,
            )
        )

        if claimed_conversation is None:
            raise ConversationAlreadyAssignedError()

        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return claimed_conversation
