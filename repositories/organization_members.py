from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.enums import OrganizationRole
from models.organization_members import OrganizationMember
from models.organizations import Organization


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


async def lock_organization(
    session: AsyncSession,
    organization_id: UUID,
) -> None:
    statement = (
        select(Organization.id)
        .where(Organization.id == organization_id)
        .with_for_update()
    )

    await session.execute(statement)


async def count_by_role(
    session: AsyncSession,
    *,
    organization_id: UUID,
    role: OrganizationRole,
) -> int:
    statement = select(func.count()).select_from(
        OrganizationMember,
    ).where(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.role == role,
    )

    return await session.scalar(statement) or 0
