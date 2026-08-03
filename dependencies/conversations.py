from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from core.exceptions import ConversationNotFoundError
from dependencies.database import SessionDep
from models.conversations import Conversation
from repositories import conversations as conversation_repository
from schemas.conversations import ConversationFilters


async def get_existing_conversation(
    conversation_id: UUID,
    session: SessionDep,
) -> Conversation:
    conversation = await conversation_repository.get_by_id(
        session=session,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise ConversationNotFoundError()

    return conversation


ExistingConversationDep = Annotated[
    Conversation,
    Depends(get_existing_conversation),
]

ConversationFiltersQuery = Annotated[
    ConversationFilters,
    Query(),
]
