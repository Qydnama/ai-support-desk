from fastapi import APIRouter, Response, status

from dependencies.conversations import (
    ConversationCreatePermissionDep,
    ConversationFiltersQuery,
    ConversationListPermissionDep,
    ConversationReadPermissionDep,
    ConversationUpdatePermissionDep,
    ExistingConversationDep,
    MessageCreatePermissionDep,
    MessageReadPermissionDep,
)
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from dependencies.pagination import PaginationDep
from repositories import conversations as conversation_repository
from repositories import messages as message_repository
from schemas.conversations import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
)
from schemas.messages import MessageCreate, MessageRead
from services import conversations as conversation_service
from services import messages as message_service

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List conversations",
)
async def list_conversations(
    filters: ConversationFiltersQuery,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _permission: ConversationListPermissionDep,
    session: SessionDep,
) -> list[ConversationRead]:
    conversations = await conversation_repository.list_by_organization(
        session=session,
        organization_id=filters.organization_id,
        user_id=current_user.id,
        status=filters.status,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return [
        ConversationRead.model_validate(conversation)
        for conversation in conversations
    ]


@router.get(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a conversation",
)
async def get_conversation(
    conversation: ExistingConversationDep,
    _permission: ConversationReadPermissionDep,
) -> ConversationRead:
    return ConversationRead.model_validate(conversation)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
)
async def create_conversation(
    data: ConversationCreate,
    _permission: ConversationCreatePermissionDep,
    response: Response,
    session: SessionDep,
) -> ConversationRead:
    conversation = await conversation_service.create_conversation(
        session=session,
        data=data,
    )

    response.headers["Location"] = (
        f"/conversations/{conversation.id}"
    )

    return ConversationRead.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a conversation",
)
async def update_conversation(
    data: ConversationUpdate,
    conversation: ExistingConversationDep,
    _permission: ConversationUpdatePermissionDep,
    session: SessionDep,
) -> ConversationRead:
    updated_conversation = await conversation_service.update_conversation(
        session=session,
        conversation=conversation,
        data=data,
    )

    return ConversationRead.model_validate(updated_conversation)


@router.get(
    "/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
    summary="List conversation messages",
)
async def list_messages(
    conversation: ExistingConversationDep,
    _permission: MessageReadPermissionDep,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[MessageRead]:
    messages = await message_repository.list_by_conversation(
        session=session,
        conversation_id=conversation.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return [
        MessageRead.model_validate(message)
        for message in messages
    ]


@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation message",
)
async def create_message(
    data: MessageCreate,
    conversation: ExistingConversationDep,
    current_user: CurrentUserDep,
    _permission: MessageCreatePermissionDep,
    response: Response,
    session: SessionDep,
) -> MessageRead:
    message = await message_service.create_message(
        session=session,
        conversation=conversation,
        data=data,
        current_user=current_user,
    )

    response.headers["Location"] = (
        f"/conversations/{conversation.id}/messages/{message.id}"
    )

    return MessageRead.model_validate(message)
