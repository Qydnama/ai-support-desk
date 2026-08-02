from typing import Annotated
from uuid import UUID

from fastapi import Depends

from dependencies.database import SessionDep
from exception import OrganizationMemberNotFoundError
from models.organization_members import OrganizationMember


async def get_existing_organization_member(
    organization_id: UUID,
    user_id: UUID,
    session: SessionDep,
) -> OrganizationMember:
    membership = await session.get(
        OrganizationMember,
        (
            organization_id,
            user_id,
        ),
    )

    if membership is None:
        raise OrganizationMemberNotFoundError()

    return membership


ExistingOrganizationMemberDep = Annotated[
    OrganizationMember,
    Depends(get_existing_organization_member),
]