from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import MessageSenderType
from core.exceptions import (
    ContactNotFoundError,
    ConversationMemberRequiredError,
    UserNotFoundError,
)
from models.conversations import Conversation
from models.messages import Message
from repositories import contacts as contact_repository
from repositories import (
    organization_members as organization_member_repository,
)
from repositories import users as user_repository
from schemas.messages import MessageCreate


async def create_message(
    session: AsyncSession,
    conversation: Conversation,
    data: MessageCreate,
) -> Message:
    if data.sender_type is MessageSenderType.CONTACT:
        contact = await contact_repository.get_active_by_id(
            session=session,
            contact_id=data.author_contact_id,
            organization_id=conversation.organization_id,
        )

        if contact is None or contact.id != conversation.contact_id:
            raise ContactNotFoundError()

    if data.sender_type is MessageSenderType.AGENT:
        author = await user_repository.get_active_by_id(
            session=session,
            user_id=data.author_user_id,
        )

        if author is None:
            raise UserNotFoundError()

        membership = await organization_member_repository.get_by_ids(
            session=session,
            organization_id=conversation.organization_id,
            user_id=author.id,
        )

        if membership is None:
            raise ConversationMemberRequiredError()

    message = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        author_user_id=data.author_user_id,
        author_contact_id=data.author_contact_id,
        sender_type=data.sender_type,
        content=data.content,
    )

    session.add(message)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return message
