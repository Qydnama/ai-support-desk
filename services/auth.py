from asyncio import to_thread
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from uuid import uuid4

from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    AuthenticationRequiredError,
    UserEmailAlreadyExistsError,
)
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from database_errors import is_user_email_unique_violation
from models.refresh_sessions import RefreshSession
from models.users import User
from repositories import (
    refresh_sessions as refresh_session_repository,
)
from repositories import users as user_repository
from schemas.auth import LoginRequest, RegisterRequest
from settings import settings

_DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "O5eawVZwuWPdKI82QgIFjA$"
    "RD0FKCoL02tu4ZpAsyjGwk0ZmQg+wtsNIEXYGEhgePM"
)

@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime

async def authenticate_user(
    session: AsyncSession,
    data: LoginRequest,
) -> User:
    user = await user_repository.get_active_by_email(
        session=session,
        email=str(data.email),
    )

    password_hash = (
        user.password_hash
        if user is not None and user.password_hash is not None
        else _DUMMY_PASSWORD_HASH
    )

    password_is_valid = await to_thread(
        verify_password,
        data.password.get_secret_value(),
        password_hash,
    )

    if (
        user is None
        or user.password_hash is None
        or not password_is_valid
    ):
        raise AuthenticationRequiredError()

    return user


async def register_user(
    session: AsyncSession,
    data: RegisterRequest,
) -> User:
    password_hash = await to_thread(
        hash_password,
        data.password.get_secret_value(),
    )

    user = User(
        id=uuid4(),
        name=data.name,
        email=str(data.email),
        password_hash=password_hash,
    )

    session.add(user)

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

    return user


async def issue_tokens(
    session: AsyncSession,
    user: User,
) -> IssuedTokens:
    session_id = uuid4()
    refresh_expires_at = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days,
    )

    refresh_token = create_refresh_token(
        user_id=user.id,
        session_id=session_id,
        expires_at=refresh_expires_at,
    )

    refresh_session = RefreshSession(
        id=session_id,
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_expires_at,
    )

    session.add(refresh_session)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return IssuedTokens(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
        refresh_expires_at=refresh_expires_at,
    )


async def rotate_tokens(
    session: AsyncSession,
    refresh_token: str,
) -> IssuedTokens:
    try:
        claims = decode_refresh_token(refresh_token)
    except InvalidTokenError:
        raise AuthenticationRequiredError() from None

    refresh_session = (
        await refresh_session_repository.get_by_id_for_update(
            session=session,
            session_id=claims.session_id,
        )
    )

    now = datetime.now(UTC)

    if (
        refresh_session is None
        or refresh_session.user_id != claims.user_id
        or refresh_session.revoked_at is not None
        or refresh_session.expires_at <= now
    ):
        await session.rollback()
        raise AuthenticationRequiredError()

    received_token_hash = hash_refresh_token(
        refresh_token,
    )

    if not compare_digest(
        received_token_hash,
        refresh_session.token_hash,
    ):
        refresh_session.revoked_at = now

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        raise AuthenticationRequiredError()

    user = await user_repository.get_active_by_id(
        session=session,
        user_id=claims.user_id,
    )

    if user is None:
        refresh_session.revoked_at = now

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        raise AuthenticationRequiredError()

    rotated_refresh_token = create_refresh_token(
        user_id=user.id,
        session_id=refresh_session.id,
        expires_at=refresh_session.expires_at,
    )

    refresh_session.token_hash = hash_refresh_token(
        rotated_refresh_token,
    )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return IssuedTokens(
        access_token=create_access_token(user.id),
        refresh_token=rotated_refresh_token,
        refresh_expires_at=refresh_session.expires_at,
    )


async def revoke_refresh_session(
    session: AsyncSession,
    refresh_token: str,
) -> None:
    try:
        claims = decode_refresh_token(refresh_token)
    except InvalidTokenError:
        return

    refresh_session = (
        await refresh_session_repository.get_by_id_for_update(
            session=session,
            session_id=claims.session_id,
        )
    )

    if (
        refresh_session is None
        or refresh_session.user_id != claims.user_id
    ):
        await session.rollback()
        return

    if refresh_session.revoked_at is None:
        refresh_session.revoked_at = datetime.now(UTC)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise