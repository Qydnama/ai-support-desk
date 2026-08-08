from uuid import UUID

from fastapi import APIRouter, Response, status

from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from dependencies.organization_members import (
    ExistingOrganizationMemberDep,
    MemberCreatePermissionDep,
    MemberDeletePermissionDep,
    MemberReadPermissionDep,
    MemberRoleUpdatePermissionDep,
    OrganizationDeletePermissionDep,
    OrganizationReadPermissionDep,
    OrganizationUpdatePermissionDep,
)
from dependencies.organizations import (
    ExistingOrganizationDep,
    OrganizationFiltersQuery,
)
from dependencies.pagination import PaginationDep
from dependencies.redis import RedisDep
from dependencies.users import ExistingUserDep
from repositories import (
    organization_members as organization_member_repository,
)
from repositories import organizations as organization_repository
from schemas.organization_members import (
    OrganizationMemberListItem,
    OrganizationMemberRead,
    OrganizationMemberRoleUpdate,
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
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[OrganizationSummaryRead]:
    rows = await organization_repository.list_summaries(
        session=session,
        current_user_id=current_user.id,
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
    organization_id: UUID,
    _permission: OrganizationReadPermissionDep,
    session: SessionDep,
    redis: RedisDep,
) -> OrganizationRead:
    return await organization_service.get_organization_profile(
        session=session,
        redis=redis,
        organization_id=organization_id,
    )


@router.get(
    "/{organization_id}/members",
    status_code=status.HTTP_200_OK,
    summary="List organization members",
)
async def list_organization_members(
    existing_organization: ExistingOrganizationDep,
    _permission: MemberReadPermissionDep,
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
            role=membership.role,
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
    current_user: CurrentUserDep,
    response: Response,
    session: SessionDep,
) -> OrganizationRead:
    created_organization = (
        await organization_service.create_organization(
            session=session,
            data=organization,
            owner=current_user,
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
    _permission: MemberCreatePermissionDep,
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
    redis: RedisDep,
    _permission: OrganizationUpdatePermissionDep,
    session: SessionDep,
) -> OrganizationRead:
    updated_organization = (
        await organization_service.update_organization(
            session=session,
            redis=redis,
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
    _permission: OrganizationDeletePermissionDep,
    redis: RedisDep,
    session: SessionDep,
) -> Response:
    await organization_service.delete_organization(
        session=session,
        redis=redis,
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
    current_membership: MemberDeletePermissionDep,
    existing_membership: ExistingOrganizationMemberDep,
    session: SessionDep,
) -> Response:
    await organization_member_service.remove_member(
        session=session,
        membership=existing_membership,
        actor_membership=current_membership,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.patch(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update an organization member role",
)
async def update_organization_member_role(
    data: OrganizationMemberRoleUpdate,
    _permission: MemberRoleUpdatePermissionDep,
    existing_membership: ExistingOrganizationMemberDep,
    session: SessionDep,
) -> OrganizationMemberRead:
    membership = await organization_member_service.update_member_role(
        session=session,
        membership=existing_membership,
        role=data.role,
    )

    return OrganizationMemberRead.model_validate(membership)
