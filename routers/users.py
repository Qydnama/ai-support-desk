from fastapi import APIRouter, Response, status

from dependencies.database import SessionDep
from dependencies.pagination import PaginationDep
from dependencies.users import ExistingUserDep
from repositories import users as user_repository
from schemas.users import (
    UserCreate,
    UserRead,
    UserReplace,
    UserUpdate,
)
from services import users as user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List users",
)
async def list_users(
    pagination: PaginationDep,
    session: SessionDep,
) -> list[UserRead]:
    users = await user_repository.list_active(
        session=session,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return [
        UserRead.model_validate(user)
        for user in users
    ]


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a user",
)
async def get_user(
    existing_user: ExistingUserDep,
) -> UserRead:
    return UserRead.model_validate(existing_user)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Replace a user",
)
async def replace_user(
    existing_user: ExistingUserDep,
    replacement: UserReplace,
    session: SessionDep,
) -> UserRead:
    replaced_user = await user_service.replace_user(
        session=session,
        user=existing_user,
        data=replacement,
    )

    return UserRead.model_validate(replaced_user)


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a user",
)
async def update_user(
    update: UserUpdate,
    existing_user: ExistingUserDep,
    session: SessionDep,
) -> UserRead:
    updated_user = await user_service.update_user(
        session=session,
        user=existing_user,
        data=update,
    )

    return UserRead.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    existing_user: ExistingUserDep,
    session: SessionDep,
) -> Response:
    await user_service.delete_user(
        session=session,
        user=existing_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
async def create_user(
    user: UserCreate,
    response: Response,
    session: SessionDep,
) -> UserRead:
    created_user = await user_service.create_user(
        session=session,
        data=user,
    )

    response.headers["Location"] = (
        f"/users/{created_user.id}"
    )

    return UserRead.model_validate(created_user)