from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import MessageSenderType
from core.exceptions import (
    ContactNotFoundError,
)
from models.conversations import Conversation
from models.messages import Message
from models.users import User
from repositories import contacts as contact_repository
from schemas.messages import MessageCreate


async def create_message(
    session: AsyncSession,
    conversation: Conversation,
    data: MessageCreate,
    current_user: User,
) -> Message:
    if data.sender_type is MessageSenderType.CONTACT:
        contact = await contact_repository.get_active_by_id(
            session=session,
            contact_id=data.author_contact_id,
            organization_id=conversation.organization_id,
        )

        if contact is None or contact.id != conversation.contact_id:
            raise ContactNotFoundError()

    message = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        author_user_id=(
            current_user.id
            if data.sender_type is MessageSenderType.AGENT
            else None
        ),
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
