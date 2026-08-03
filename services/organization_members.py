from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import OrganizationMemberAlreadyExistsError
from database_errors import (
    is_organization_member_primary_key_violation,
)
from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.users import User


async def add_member(
    session: AsyncSession,
    organization: Organization,
    user: User,
) -> OrganizationMember:
    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
    )

    session.add(membership)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_member_primary_key_violation(exc):
            raise OrganizationMemberAlreadyExistsError() from exc

        raise

    return membership


async def remove_member(
    session: AsyncSession,
    membership: OrganizationMember,
) -> None:
    try:
        await session.delete(membership)
        await session.commit()
    except Exception:
        await session.rollback()
        raise