from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from core.exceptions import AuthenticationRequiredError
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
)
from schemas.users import UserRead
from services import auth as auth_service
from settings import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

RefreshTokenCookie = Annotated[
    str | None,
    Cookie(
        alias=settings.refresh_cookie_name,
    ),
]


def set_refresh_cookie(
    response: Response,
    tokens: auth_service.IssuedTokens,
) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=tokens.refresh_token,
        expires=tokens.refresh_expires_at,
        path="/auth",
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )


@router.get(
    "/me",
    summary="Get current user",
)
async def get_current_user(
    current_user: CurrentUserDep,
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register_user(
    data: RegisterRequest,
    response: Response,
    session: SessionDep,
) -> UserRead:
    user = await auth_service.register_user(
        session=session,
        data=data,
    )

    response.headers["Location"] = f"/users/{user.id}"

    return UserRead.model_validate(user)


@router.post(
    "/login",
    summary="Log in",
)
async def login_user(
    data: LoginRequest,
    response: Response,
    session: SessionDep,
) -> AccessTokenResponse:
    user = await auth_service.authenticate_user(
        session=session,
        data=data,
    )

    tokens = await auth_service.issue_tokens(
        session=session,
        user=user,
    )

    set_refresh_cookie(
        response=response,
        tokens=tokens,
    )

    return AccessTokenResponse(
        access_token=tokens.access_token,
    )


@router.post(
    "/refresh",
    summary="Refresh authentication tokens",
)
async def refresh_tokens(
    response: Response,
    session: SessionDep,
    refresh_token: RefreshTokenCookie = None,
) -> AccessTokenResponse:
    if refresh_token is None:
        raise AuthenticationRequiredError()

    tokens = await auth_service.rotate_tokens(
        session=session,
        refresh_token=refresh_token,
    )

    set_refresh_cookie(
        response=response,
        tokens=tokens,
    )

    return AccessTokenResponse(
        access_token=tokens.access_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
)
async def logout_user(
    response: Response,
    session: SessionDep,
    refresh_token: RefreshTokenCookie = None,
) -> None:
    if refresh_token is not None:
        await auth_service.revoke_refresh_session(
            session=session,
            refresh_token=refresh_token,
        )

    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/auth",
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="lax",
    )