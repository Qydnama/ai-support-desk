from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import OrganizationSlugAlreadyExistsError
from database_errors import is_organization_slug_unique_violation
from models.organizations import Organization
from schemas.organizations import (
    OrganizationCreate,
    OrganizationUpdate,
)


async def create_organization(
    session: AsyncSession,
    data: OrganizationCreate,
) -> Organization:
    organization = Organization(
        id=uuid4(),
        **data.model_dump(),
    )

    session.add(organization)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_slug_unique_violation(exc):
            raise OrganizationSlugAlreadyExistsError() from exc

        raise

    return organization


async def update_organization(
    session: AsyncSession,
    organization: Organization,
    data: OrganizationUpdate,
) -> Organization:
    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        organization.name = update_data["name"]

    if "slug" in update_data:
        organization.slug = update_data["slug"]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_slug_unique_violation(exc):
            raise OrganizationSlugAlreadyExistsError() from exc

        raise

    return organization


async def delete_organization(
    session: AsyncSession,
    organization: Organization,
) -> None:
    try:
        await session.delete(organization)
        await session.commit()
    except Exception:
        await session.rollback()
        raise