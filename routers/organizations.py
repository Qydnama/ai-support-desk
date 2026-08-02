from uuid import uuid4

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from database_errors import (
    is_organization_member_primary_key_violation,
    is_organization_slug_unique_violation,
)
from dependencies.database import SessionDep
from dependencies.organization_members import (
    ExistingOrganizationMemberDep,
)
from dependencies.organizations import (
    ExistingOrganizationDep,
    OrganizationFiltersDep,
)
from dependencies.pagination import PaginationDep
from dependencies.users import ExistingUserDep
from exception import (
    OrganizationMemberAlreadyExistsError,
    OrganizationSlugAlreadyExistsError,
)
from models.organization_members import OrganizationMember
from models.organizations import Organization
from schemas.organization_members import (
    OrganizationMemberListItem,
    OrganizationMemberRead,
)
from schemas.organizations import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationSummaryRead,
    OrganizationUpdate,
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List organizations",
)
async def list_organizations(
    filters: OrganizationFiltersDep,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[OrganizationSummaryRead]:
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

    if filters.name is not None:
        statement = statement.where(
            Organization.name == filters.name,
        )

    if filters.slug is not None:
        statement = statement.where(
            Organization.slug == filters.slug,
        )

    if filters.member_user_id is not None:
        statement = statement.where(
            Organization.memberships.any(
                OrganizationMember.user_id
                == filters.member_user_id,
            ),
        )

    statement = statement.group_by(
        Organization.id,
        Organization.name,
        Organization.slug,
    )

    if filters.min_members is not None:
        statement = statement.having(
            member_count >= filters.min_members,
        )

    statement = (
        statement
        .order_by(Organization.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    rows = await session.execute(statement)

    return [
        OrganizationSummaryRead(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            member_count=count,
        )
        for organization, count in rows
    ]


@router.get(
    "/{organization_id}",
    status_code=status.HTTP_200_OK,
    summary="Get an organization",
)
async def get_organization(
    existing_organization: ExistingOrganizationDep,
) -> OrganizationRead:
    return OrganizationRead.model_validate(
        existing_organization,
    )


@router.get(
    "/{organization_id}/members",
    status_code=status.HTTP_200_OK,
    summary="List organization members",
)
async def list_organization_members(
    existing_organization: ExistingOrganizationDep,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[OrganizationMemberListItem]:
    statement = (
        select(OrganizationMember)
        .options(
            joinedload(OrganizationMember.user),
        )
        .where(
            OrganizationMember.organization_id == existing_organization.id,
        )
        .order_by(OrganizationMember.user_id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    memberships = await session.scalars(statement)

    return [
        OrganizationMemberListItem(
            user_id=membership.user_id,
            name=(
                "Deleted user"
                if membership.user.deleted_at is not None
                else membership.user.name
            ),
            is_deleted=membership.user.deleted_at is not None,
        )
        for membership in memberships
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization",
)
async def create_organization(
    organization: OrganizationCreate,
    response: Response,
    session: SessionDep,
) -> OrganizationRead:
    created_organization = Organization(
        id=uuid4(),
        **organization.model_dump(),
    )

    session.add(created_organization)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_slug_unique_violation(exc):
            raise OrganizationSlugAlreadyExistsError() from exc

        raise

    response.headers["Location"] = f"/organizations/{created_organization.id}"

    return OrganizationRead.model_validate(
        created_organization,
    )


@router.post(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add an organization member",
)
async def add_organization_member(
    existing_organization: ExistingOrganizationDep,
    existing_user: ExistingUserDep,
    response: Response,
    session: SessionDep,
) -> OrganizationMemberRead:
    membership = OrganizationMember(
        organization_id=existing_organization.id,
        user_id=existing_user.id,
    )

    session.add(membership)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_member_primary_key_violation(exc):
            raise OrganizationMemberAlreadyExistsError() from exc

        raise

    response.headers["Location"] = (
        f"/organizations/{existing_organization.id}/members/{existing_user.id}"
    )

    return OrganizationMemberRead.model_validate(
        membership,
    )


@router.patch(
    "/{organization_id}",
    status_code=status.HTTP_200_OK,
    summary="Update an organization",
)
async def update_organization(
    update: OrganizationUpdate,
    existing_organization: ExistingOrganizationDep,
    session: SessionDep,
) -> OrganizationRead:
    update_data = update.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        existing_organization.name = update_data["name"]

    if "slug" in update_data:
        existing_organization.slug = update_data["slug"]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_organization_slug_unique_violation(exc):
            raise OrganizationSlugAlreadyExistsError() from exc

        raise

    return OrganizationRead.model_validate(
        existing_organization,
    )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an organization",
)
async def delete_organization(
    existing_organization: ExistingOrganizationDep,
    session: SessionDep,
) -> Response:
    await session.delete(existing_organization)
    await session.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an organization member",
)
async def remove_organization_member(
    existing_membership: ExistingOrganizationMemberDep,
    session: SessionDep,
) -> Response:
    await session.delete(existing_membership)
    await session.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
