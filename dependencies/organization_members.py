from typing import Annotated
from uuid import UUID

from fastapi import Depends

from core.exceptions import OrganizationMemberNotFoundError
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


ExistingOrganizationMemberDep = Annotated[
    OrganizationMember,
    Depends(get_existing_organization_member),
]