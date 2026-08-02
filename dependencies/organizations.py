from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from sqlalchemy import select

from dependencies.database import SessionDep
from exception import OrganizationNotFoundError
from models.organizations import Organization
from schemas.organizations import OrganizationFilters


async def get_existing_organization(
    organization_id: UUID,
    session: SessionDep,
) -> Organization:
    statement = select(Organization).where(
        Organization.id == organization_id,
    )

    organization = await session.scalar(statement)

    if organization is None:
        raise OrganizationNotFoundError()

    return organization


ExistingOrganizationDep = Annotated[
    Organization,
    Depends(get_existing_organization),
]

OrganizationFiltersDep = Annotated[
    OrganizationFilters,
    Query(),
]