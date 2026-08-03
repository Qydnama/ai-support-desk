from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.organization_members import OrganizationMember
from models.organizations import Organization


async def get_by_id(
    session: AsyncSession,
    organization_id: UUID,
) -> Organization | None:
    return await session.get(
        Organization,
        organization_id,
    )


async def list_summaries(
    session: AsyncSession,
    *,
    name: str | None,
    slug: str | None,
    member_user_id: UUID | None,
    min_members: int | None,
    limit: int,
    offset: int,
) -> list[tuple[Organization, int]]:
    member_count = func.count(
        OrganizationMember.user_id,
    ).label("member_count")

    statement = (
        select(
            Organization,
            member_count,
        )
        .outerjoin(
            OrganizationMember,
            OrganizationMember.organization_id
            == Organization.id,
        )
    )

    if name is not None:
        statement = statement.where(
            Organization.name == name,
        )

    if slug is not None:
        statement = statement.where(
            Organization.slug == slug,
        )

    if member_user_id is not None:
        statement = statement.where(
            Organization.memberships.any(
                OrganizationMember.user_id == member_user_id,
            ),
        )

    statement = statement.group_by(
        Organization.id,
        Organization.name,
        Organization.slug,
    )

    if min_members is not None:
        statement = statement.having(
            member_count >= min_members,
        )

    statement = (
        statement
        .order_by(Organization.id)
        .offset(offset)
        .limit(limit)
    )

    rows = await session.execute(statement)

    return [
        (organization, count)
        for organization, count in rows
    ]