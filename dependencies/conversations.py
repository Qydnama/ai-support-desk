from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from core.enums import OrganizationPermission
from core.exceptions import (
    ConversationNotFoundError,
    OrganizationMemberRequiredError,
    OrganizationPermissionDeniedError,
)
from core.permissions import ROLE_PERMISSIONS
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from models.conversations import Conversation
from models.organization_members import OrganizationMember
from repositories import (
    organization_members as organization_member_repository,
)
from repositories import conversations as conversation_repository
from schemas.conversations import ConversationCreate, ConversationFilters


async def get_existing_conversation(
    conversation_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> Conversation:
    conversation = await conversation_repository.get_by_id_for_user(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user.id,
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


async def _require_organization_permission(
    session: SessionDep,
    *,
    organization_id: UUID,
    user_id: UUID,
    permission: OrganizationPermission,
) -> OrganizationMember:
    membership = await organization_member_repository.get_by_ids(
        session=session,
        organization_id=organization_id,
        user_id=user_id,
    )

    if membership is None:
        raise OrganizationMemberRequiredError()

    if permission not in ROLE_PERMISSIONS[membership.role]:
        raise OrganizationPermissionDeniedError()

    return membership


async def require_conversation_list_permission(
    filters: ConversationFiltersQuery,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> OrganizationMember:
    return await _require_organization_permission(
        session=session,
        organization_id=filters.organization_id,
        user_id=current_user.id,
        permission=OrganizationPermission.CONVERSATION_READ,
    )


async def require_conversation_create_permission(
    data: ConversationCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> OrganizationMember:
    return await _require_organization_permission(
        session=session,
        organization_id=data.organization_id,
        user_id=current_user.id,
        permission=OrganizationPermission.CONVERSATION_CREATE,
    )


def require_conversation_permission(
    permission: OrganizationPermission,
) -> Callable[..., Awaitable[OrganizationMember]]:
    async def require_permission(
        conversation: ExistingConversationDep,
        current_user: CurrentUserDep,
        session: SessionDep,
    ) -> OrganizationMember:
        return await _require_organization_permission(
            session=session,
            organization_id=conversation.organization_id,
            user_id=current_user.id,
            permission=permission,
        )

    return require_permission


ConversationListPermissionDep = Annotated[
    OrganizationMember,
    Depends(require_conversation_list_permission),
]


ConversationCreatePermissionDep = Annotated[
    OrganizationMember,
    Depends(require_conversation_create_permission),
]


ConversationReadPermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_conversation_permission(
            OrganizationPermission.CONVERSATION_READ,
        ),
    ),
]


ConversationUpdatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_conversation_permission(
            OrganizationPermission.CONVERSATION_UPDATE,
        ),
    ),
]


MessageReadPermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_conversation_permission(
            OrganizationPermission.MESSAGE_READ,
        ),
    ),
]


MessageCreatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_conversation_permission(
            OrganizationPermission.MESSAGE_CREATE,
        ),
    ),
]
