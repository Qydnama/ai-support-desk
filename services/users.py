from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import UserEmailAlreadyExistsError
from database_errors import is_user_email_unique_violation
from models.users import User
from schemas.users import (
    UserCreate,
    UserReplace,
    UserUpdate,
)


async def _commit(
    session: AsyncSession,
) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_user_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError() from exc

        raise
    except Exception:
        await session.rollback()
        raise


async def create_user(
    session: AsyncSession,
    data: UserCreate,
) -> User:
    user = User(
        id=uuid4(),
        **data.model_dump(),
    )

    session.add(user)
    await _commit(session)

    return user


async def replace_user(
    session: AsyncSession,
    user: User,
    data: UserReplace,
) -> User:
    user.name = data.name
    user.email = data.email

    await _commit(session)

    return user


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdate,
) -> User:
    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        user.name = update_data["name"]

    if "email" in update_data:
        user.email = update_data["email"]

    await _commit(session)

    return user


async def delete_user(
    session: AsyncSession,
    user: User,
) -> None:
    user.deleted_at = datetime.now(UTC)

    await _commit(session)