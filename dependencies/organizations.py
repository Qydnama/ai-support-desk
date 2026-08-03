from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from core.exceptions import OrganizationNotFoundError
from dependencies.database import SessionDep
from models.organizations import Organization
from repositories import organizations as organization_repository
from schemas.organizations import OrganizationFilters


async def get_existing_organization(
    organization_id: UUID,
    session: SessionDep,
) -> Organization:
    organization = await organization_repository.get_by_id(
        session=session,
        organization_id=organization_id,
    )

    if organization is None:
        raise OrganizationNotFoundError()

    return organization


ExistingOrganizationDep = Annotated[
    Organization,
    Depends(get_existing_organization),
]

OrganizationFiltersQuery = Annotated[
    OrganizationFilters,
    Query(),
]