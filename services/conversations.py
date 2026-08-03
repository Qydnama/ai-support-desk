from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    ContactNotFoundError,
    ConversationMemberRequiredError,
    OrganizationNotFoundError,
    UserNotFoundError,
)
from models.conversations import Conversation
from repositories import contacts as contact_repository
from repositories import (
    organization_members as organization_member_repository,
)
from repositories import organizations as organization_repository
from repositories import users as user_repository
from schemas.conversations import (
    ConversationCreate,
    ConversationUpdate,
)


async def _require_active_member(
    session: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> None:
    user = await user_repository.get_active_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundError()

    membership = await organization_member_repository.get_by_ids(
        session=session,
        organization_id=organization_id,
        user_id=user_id,
    )

    if membership is None:
        raise ConversationMemberRequiredError()


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
    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data:
        conversation.status = update_data["status"]

    if "assigned_user_id" in update_data:
        assigned_user_id = update_data["assigned_user_id"]

        if assigned_user_id is not None:
            await _require_active_member(
                session=session,
                organization_id=conversation.organization_id,
                user_id=assigned_user_id,
            )

        conversation.assigned_user_id = assigned_user_id

    conversation.updated_at = datetime.now(UTC)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return conversation
