from uuid import UUID, uuid4

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from dependencies.database import SessionDep
from dependencies.pagination import PaginationDep
from exception import UserEmailAlreadyExistsError, UserNotFoundError
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
    user_id: UUID,
    session: SessionDep,
) -> UserRead:
    user = await session.get(User, user_id)

    if user is None:
        raise UserNotFoundError()

    return UserRead.model_validate(user)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Replace a user",
)
async def replace_user(
    user_id: UUID,
    replacement: UserReplace,
    session: SessionDep,
) -> UserRead:
    user = await session.get(User, user_id)

    if user is None:
        raise UserNotFoundError()

    user.name = replacement.name
    user.email = replacement.email

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise UserEmailAlreadyExistsError() from exc

    return UserRead.model_validate(user)


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a user",
)
async def update_user(
    user_id: UUID,
    update: UserUpdate,
    session: SessionDep,
) -> UserRead:
    user = await session.get(User, user_id)

    if user is None:
        raise UserNotFoundError()

    update_data = update.model_dump(exclude_unset=True)

    if "name" in update_data:
        user.name = update_data["name"]

    if "email" in update_data:
        user.email = update_data["email"]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise UserEmailAlreadyExistsError() from exc

    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    user_id: UUID,
    session: SessionDep,
) -> Response:
    user = await session.get(User, user_id)

    if user is None:
        raise UserNotFoundError()

    await session.delete(user)
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
        raise UserEmailAlreadyExistsError() from exc

    response.headers["Location"] = f"/users/{created_user.id}"

    return UserRead.model_validate(created_user)
