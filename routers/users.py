from uuid import uuid4

from fastapi import APIRouter, Response, status

from dependencies.pagination import PaginationDep
from dependencies.users import ExistingUserDep
from exception import UserEmailAlreadyExistsError
from schemas.users import UserCreate, UserRead, UserReplace, UserUpdate
from storage.users import is_email_taken, users_by_id

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
) -> list[UserRead]:
    users = list(users_by_id.values())

    return users[
        pagination.offset : pagination.offset + pagination.limit
    ]


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a user",
)
async def get_user(existing_user: ExistingUserDep) -> UserRead:
    return existing_user


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Replace a user",
)
async def replace_user(
    replacement: UserReplace,
    existing_user: ExistingUserDep,
) -> UserRead:

    if is_email_taken(
        replacement.email,
        excluding_user_id=existing_user.id,
    ):
        raise UserEmailAlreadyExistsError()

    replaced_user = UserRead(
        id=existing_user.id,
        **replacement.model_dump(),
    )

    users_by_id[existing_user.id] = replaced_user

    return replaced_user


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a user",
)
async def update_user(
    existing_user: ExistingUserDep,
    update: UserUpdate,
) -> UserRead:

    update_data = update.model_dump(exclude_unset=True)

    if "email" in update_data:
        updated_email = update_data["email"]

        if is_email_taken(
            updated_email,
            excluding_user_id=existing_user.id,
        ):
            raise UserEmailAlreadyExistsError()

    merged_data = existing_user.model_dump() | update_data
    updated_user = UserRead.model_validate(merged_data)

    users_by_id[existing_user.id] = updated_user

    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(existing_user: ExistingUserDep) -> Response:
    del users_by_id[existing_user.id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
async def create_user(
    user: UserCreate,
    response: Response,
) -> UserRead:
    if is_email_taken(user.email):
        raise UserEmailAlreadyExistsError()

    created_user = UserRead(
        id=uuid4(),
        **user.model_dump(),
    )

    users_by_id[created_user.id] = created_user
    response.headers["Location"] = f"/users/{created_user.id}"

    return created_user
