from typing import Annotated
from uuid import UUID

from fastapi import Depends

from core.exceptions import UserNotFoundError
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from models.users import User
from repositories import users as user_repository


async def get_existing_user(
    user_id: UUID,
    session: SessionDep,
) -> User:
    user = await user_repository.get_active_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundError()

    return user


ExistingUserDep = Annotated[
    User,
    Depends(get_existing_user),
]


async def get_current_user_account(
    user_id: UUID,
    current_user: CurrentUserDep,
) -> User:
    if current_user.id != user_id:
        raise UserNotFoundError()

    return current_user


CurrentUserAccountDep = Annotated[
    User,
    Depends(get_current_user_account),
]
