from typing import Annotated
from uuid import UUID

from fastapi import Depends

from exception import UserNotFoundError
from schemas.users import UserRead
from storage.users import users_by_id


async def get_existing_user(
    user_id: UUID,
) -> UserRead:
    user = users_by_id.get(user_id)

    if user is None:
        raise UserNotFoundError()

    return user


ExistingUserDep = Annotated[
    UserRead,
    Depends(get_existing_user),
]