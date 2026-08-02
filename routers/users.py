from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database_errors import is_user_email_unique_violation
from dependencies.database import SessionDep
from dependencies.pagination import PaginationDep
from dependencies.users import ExistingUserDep
from exception import UserEmailAlreadyExistsError
from models.users import User
from schemas.users import UserCreate, UserRead, UserReplace, UserUpdate

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
    statement = (
        select(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    users = await session.scalars(statement)

    return list(users)


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
    existing_user.name = replacement.name
    existing_user.email = replacement.email

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_user_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError() from exc

        raise

    return UserRead.model_validate(existing_user)


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
    update_data = update.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_user.name = update_data["name"]

    if "email" in update_data:
        existing_user.email = update_data["email"]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_user_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError() from exc

        raise

    return UserRead.model_validate(existing_user)



@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    existing_user: ExistingUserDep,
    session: SessionDep,
) -> Response:
    existing_user.deleted_at = datetime.now(UTC)

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    created_user = User(
        id=uuid4(),
        **user.model_dump(),
    )

    session.add(created_user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_user_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError() from exc

        raise

    response.headers["Location"] = f"/users/{created_user.id}"

    return UserRead.model_validate(created_user)
