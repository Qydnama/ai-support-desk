from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import OrganizationRole
from core.exceptions import (
    LastOrganizationOwnerError,
    OrganizationMemberAlreadyExistsError,
    OrganizationPermissionDeniedError,
)
from database_errors import (
    is_organization_member_primary_key_violation,
)
from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.users import User
from repositories import (
    organization_members as organization_member_repository,
)


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
    actor_membership: OrganizationMember,
) -> None:
    try:
        await organization_member_repository.lock_organization(
            session=session,
            organization_id=membership.organization_id,
        )
        await session.refresh(membership)
        await session.refresh(actor_membership)

        if (
            actor_membership.role is OrganizationRole.ADMIN
            and membership.role is not OrganizationRole.AGENT
        ):
            raise OrganizationPermissionDeniedError()

        if membership.role is OrganizationRole.OWNER:
            owner_count = await organization_member_repository.count_by_role(
                session=session,
                organization_id=membership.organization_id,
                role=OrganizationRole.OWNER,
            )

            if owner_count <= 1:
                raise LastOrganizationOwnerError()

        await session.delete(membership)
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def update_member_role(
    session: AsyncSession,
    membership: OrganizationMember,
    role: OrganizationRole,
) -> OrganizationMember:
    try:
        await organization_member_repository.lock_organization(
            session=session,
            organization_id=membership.organization_id,
        )
        await session.refresh(membership)

        if (
            membership.role is OrganizationRole.OWNER
            and role is not OrganizationRole.OWNER
        ):
            owner_count = await organization_member_repository.count_by_role(
                session=session,
                organization_id=membership.organization_id,
                role=OrganizationRole.OWNER,
            )

            if owner_count <= 1:
                raise LastOrganizationOwnerError()

        membership.role = role
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return membership
