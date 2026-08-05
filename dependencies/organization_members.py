from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from core.enums import OrganizationPermission
from core.exceptions import (
    OrganizationMemberNotFoundError,
    OrganizationMemberRequiredError,
    OrganizationPermissionDeniedError,
)
from core.permissions import ROLE_PERMISSIONS
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from models.organization_members import OrganizationMember
from repositories import (
    organization_members as organization_member_repository,
)


async def get_existing_organization_member(
    organization_id: UUID,
    user_id: UUID,
    session: SessionDep,
) -> OrganizationMember:
    membership = await organization_member_repository.get_by_ids(
        session=session,
        organization_id=organization_id,
        user_id=user_id,
    )

    if membership is None:
        raise OrganizationMemberNotFoundError()

    return membership


async def get_current_organization_member(
    organization_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> OrganizationMember:
    membership = await organization_member_repository.get_by_ids(
        session=session,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    if membership is None:
        raise OrganizationMemberRequiredError()

    return membership


def require_organization_permission(
    required_permission: OrganizationPermission,
) -> Callable[
    [OrganizationMember],
    Awaitable[OrganizationMember],
]:
    async def require_permission(
        current_membership: CurrentOrganizationMemberDep,
    ) -> OrganizationMember:
        permissions = ROLE_PERMISSIONS[current_membership.role]

        if required_permission not in permissions:
            raise OrganizationPermissionDeniedError()

        return current_membership

    return require_permission


ExistingOrganizationMemberDep = Annotated[
    OrganizationMember,
    Depends(get_existing_organization_member),
]


CurrentOrganizationMemberDep = Annotated[
    OrganizationMember,
    Depends(get_current_organization_member),
]


OrganizationReadPermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.ORGANIZATION_READ,
        ),
    ),
]


OrganizationUpdatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.ORGANIZATION_UPDATE,
        ),
    ),
]


OrganizationDeletePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.ORGANIZATION_DELETE,
        ),
    ),
]


MemberReadPermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.MEMBER_READ,
        ),
    ),
]


MemberCreatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.MEMBER_CREATE,
        ),
    ),
]


MemberDeletePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.MEMBER_DELETE,
        ),
    ),
]


MemberRoleUpdatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.MEMBER_ROLE_UPDATE,
        ),
    ),
]


ContactReadPermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.CONTACT_READ,
        ),
    ),
]


ContactCreatePermissionDep = Annotated[
    OrganizationMember,
    Depends(
        require_organization_permission(
            OrganizationPermission.CONTACT_CREATE,
        ),
    ),
]
