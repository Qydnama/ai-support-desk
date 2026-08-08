import logging
from random import randint
from uuid import UUID, uuid4

from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import OrganizationRole
from core.exceptions import (
    OrganizationMemberRequiredError,
    OrganizationSlugAlreadyExistsError,
)
from database_errors import is_organization_slug_unique_violation
from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.users import User
from repositories import organizations as organization_repository
from schemas.organizations import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)

logger = logging.getLogger(__name__)

ORGANIZATION_PROFILE_CACHE_TTL_SECONDS = 300
ORGANIZATION_PROFILE_CACHE_TTL_JITTER_SECONDS = 30


def organization_profile_cache_key(
    organization_id: UUID,
) -> str:
    return f"cache:organization:v1:{organization_id}"


async def invalidate_organization_profile(
    *,
    redis: Redis,
    organization_id: UUID,
) -> None:
    try:
        await redis.delete(
            organization_profile_cache_key(organization_id),
        )
    except RedisError:
        logger.warning(
            "Could not invalidate organization profile cache",
            exc_info=True,
        )


async def get_organization_profile(
    *,
    session: AsyncSession,
    redis: Redis,
    organization_id: UUID,
) -> OrganizationRead:
    cache_key = organization_profile_cache_key(organization_id)

    try:
        cached_profile = await redis.get(cache_key)
    except RedisError:
        logger.warning(
            "Could not read organization profile cache",
            exc_info=True,
        )
    else:
        if cached_profile is not None:
            try:
                return OrganizationRead.model_validate_json(
                    cached_profile,
                )
            except ValidationError:
                logger.warning(
                    "Discarding invalid organization profile cache value",
                )
                await invalidate_organization_profile(
                    redis=redis,
                    organization_id=organization_id,
                )

    organization = await organization_repository.get_by_id(
        session=session,
        organization_id=organization_id,
    )

    if organization is None:
        raise OrganizationMemberRequiredError()

    profile = OrganizationRead.model_validate(organization)

    ttl = (
        ORGANIZATION_PROFILE_CACHE_TTL_SECONDS
        + randint(
            0,
            ORGANIZATION_PROFILE_CACHE_TTL_JITTER_SECONDS,
        )
    )

    try:
        await redis.set(
            cache_key,
            profile.model_dump_json(),
            ex=ttl,
        )
    except RedisError:
        logger.warning(
            "Could not write organization profile cache",
            exc_info=True,
        )

    return profile


async def create_organization(
    session: AsyncSession,
    data: OrganizationCreate,
    owner: User,
) -> Organization:
    organization = Organization(
        id=uuid4(),
        **data.model_dump(),
    )

    owner_membership = OrganizationMember(
        organization_id=organization.id,
        user_id=owner.id,
        role=OrganizationRole.OWNER,
    )

    session.add_all([
        organization,
        owner_membership,
    ])

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
    redis: Redis,
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

    await invalidate_organization_profile(
        redis=redis,
        organization_id=organization.id,
    )

    return organization


async def delete_organization(
    session: AsyncSession,
    redis: Redis,
    organization: Organization,
) -> None:
    organization_id = organization.id
    try:
        await session.delete(organization)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    await invalidate_organization_profile(
        redis=redis,
        organization_id=organization_id,
    )