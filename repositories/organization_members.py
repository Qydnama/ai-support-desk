from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.organization_members import OrganizationMember


async def get_by_ids(
    session: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> OrganizationMember | None:
    return await session.get(
        OrganizationMember,
        (
            organization_id,
            user_id,
        ),
    )


async def list_by_organization(
    session: AsyncSession,
    *,
    organization_id: UUID,
    limit: int,
    offset: int,
) -> list[OrganizationMember]:
    statement = (
        select(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
        )
        .where(
            OrganizationMember.organization_id == organization_id,
        )
        .order_by(OrganizationMember.user_id)
        .offset(offset)
        .limit(limit)
    )

    memberships = await session.scalars(statement)

    return list(memberships)