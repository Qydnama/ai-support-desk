import json
from hashlib import sha256
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import MessageSenderType
from core.exceptions import (
    ContactNotFoundError,
    IdempotencyKeyConflictError,
)
from database_errors import (
    is_idempotency_record_organization_key_unique_violation,
)
from models.conversations import Conversation
from models.idempotency_records import IdempotencyRecord
from models.messages import Message
from models.users import User
from repositories import contacts as contact_repository
from repositories import idempotency_records as idempotency_repository
from schemas.messages import MessageCreate


def _create_request_fingerprint(
    *,
    conversation: Conversation,
    data: MessageCreate,
    current_user: User,
) -> str:
    payload = {
        "conversation_id": str(conversation.id),
        "sender_type": data.sender_type.value,
        "actor_user_id": str(current_user.id),
        "author_contact_id": (
            str(data.author_contact_id)
            if data.author_contact_id is not None
            else None
        ),
        "content": data.content,
    }

    encoded_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return sha256(encoded_payload).hexdigest()


async def create_message(
    session: AsyncSession,
    conversation: Conversation,
    data: MessageCreate,
    current_user: User,
    idempotency_key: str,
) -> Message:
    organization_id = conversation.organization_id
    
    request_fingerprint = _create_request_fingerprint(
        conversation=conversation,
        data=data,
        current_user=current_user,
    )

    existing_record = await idempotency_repository.get_by_key(
        session,
        organization_id=organization_id,
        key=idempotency_key,
    )

    if existing_record is not None:
        if existing_record.request_fingerprint != request_fingerprint:
            await session.rollback()
            raise IdempotencyKeyConflictError()

        return existing_record.message

    if data.sender_type is MessageSenderType.CONTACT:
        contact = await contact_repository.get_active_by_id(
            session=session,
            organization_id=organization_id,
            contact_id=data.author_contact_id,
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

    idempotency_record = IdempotencyRecord(
        id=uuid4(),
        organization_id=organization_id,
        key=idempotency_key,
        request_fingerprint=request_fingerprint,
        message_id=message.id,
        message=message,
    )

    session.add_all([message, idempotency_record])

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if not is_idempotency_record_organization_key_unique_violation(
            exc
        ):
            raise

        existing_record = await idempotency_repository.get_by_key(
            session,
            organization_id=organization_id,
            key=idempotency_key,
        )

        if existing_record is None:
            raise

        if existing_record.request_fingerprint != request_fingerprint:
            await session.rollback()
            raise IdempotencyKeyConflictError() from exc

        return existing_record.message
    except Exception:
        await session.rollback()
        raise

    return message