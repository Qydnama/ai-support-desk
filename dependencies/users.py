from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select

from dependencies.database import SessionDep
from exception import UserNotFoundError
from models.users import User


async def get_existing_user(
    user_id: UUID,
    session: SessionDep,
) -> User:
    statement = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),
    )

    user = await session.scalar(statement)

    if user is None:
        raise UserNotFoundError()

    return user


ExistingUserDep = Annotated[
    User,
    Depends(get_existing_user),
]