from fastapi import APIRouter, Response, status

from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from dependencies.users import CurrentUserAccountDep
from schemas.users import (
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
    current_user: CurrentUserDep,
) -> list[UserRead]:
    return [
        UserRead.model_validate(current_user),
    ]


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a user",
)
async def get_user(
    current_user: CurrentUserAccountDep,
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Replace a user",
)
async def replace_user(
    current_user: CurrentUserAccountDep,
    replacement: UserReplace,
    session: SessionDep,
) -> UserRead:
    replaced_user = await user_service.replace_user(
        session=session,
        user=current_user,
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
    current_user: CurrentUserAccountDep,
    session: SessionDep,
) -> UserRead:
    updated_user = await user_service.update_user(
        session=session,
        user=current_user,
        data=update,
    )

    return UserRead.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    current_user: CurrentUserAccountDep,
    session: SessionDep,
) -> Response:
    await user_service.delete_user(
        session=session,
        user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
