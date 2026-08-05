from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import InvalidTokenError

from core.exceptions import AuthenticationRequiredError
from core.security import decode_access_token
from dependencies.database import SessionDep
from models.users import User
from repositories import users as user_repository

bearer_scheme = HTTPBearer(
    auto_error=False,
)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: SessionDep,
) -> User:
    if credentials is None:
        raise AuthenticationRequiredError()

    try:
        user_id = decode_access_token(
            credentials.credentials,
        )
    except InvalidTokenError:
        raise AuthenticationRequiredError() from None

    user = await user_repository.get_active_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        raise AuthenticationRequiredError()

    return user


CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]