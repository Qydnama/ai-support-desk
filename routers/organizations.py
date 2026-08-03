from fastapi import APIRouter, Response, status

from dependencies.database import SessionDep
from dependencies.organization_members import (
    ExistingOrganizationMemberDep,
)
from dependencies.organizations import (
    ExistingOrganizationDep,
    OrganizationFiltersQuery,
)
from dependencies.pagination import PaginationDep
from dependencies.users import ExistingUserDep
from repositories import (
    organization_members as organization_member_repository,
)
from repositories import organizations as organization_repository
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
from services import (
    organization_members as organization_member_service,
)
from services import organizations as organization_service

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
    filters: OrganizationFiltersQuery,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[OrganizationSummaryRead]:
    rows = await organization_repository.list_summaries(
        session=session,
        name=filters.name,
        slug=filters.slug,
        member_user_id=filters.member_user_id,
        min_members=filters.min_members,
        limit=pagination.limit,
        offset=pagination.offset,
    )

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
    memberships = (
        await organization_member_repository.list_by_organization(
            session=session,
            organization_id=existing_organization.id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )

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
    created_organization = (
        await organization_service.create_organization(
            session=session,
            data=organization,
        )
    )

    response.headers["Location"] = (
        f"/organizations/{created_organization.id}"
    )

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
    membership = await organization_member_service.add_member(
        session=session,
        organization=existing_organization,
        user=existing_user,
    )

    response.headers["Location"] = (
        f"/organizations/{existing_organization.id}"
        f"/members/{existing_user.id}"
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
    updated_organization = (
        await organization_service.update_organization(
            session=session,
            organization=existing_organization,
            data=update,
        )
    )

    return OrganizationRead.model_validate(
        updated_organization,
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
    await organization_service.delete_organization(
        session=session,
        organization=existing_organization,
    )

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
    await organization_member_service.remove_member(
        session=session,
        membership=existing_membership,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )