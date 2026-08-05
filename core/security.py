from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from settings import settings

_password_hash = PasswordHash.recommended()

@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    user_id: UUID
    session_id: UUID


def hash_password(plain_password: str) -> str:
    return _password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    return _password_hash.verify(
        plain_password,
        password_hash,
    )


def create_access_token(
    user_id: UUID,
) -> str:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
        "token_type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
) -> UUID:
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": [
                "sub",
                "iat",
                "exp",
                "jti",
                "token_type",
            ],
        },
    )

    if payload["token_type"] != "access":
        raise InvalidTokenError(
            "Token is not an access token",
        )

    try:
        user_id = UUID(payload["sub"])
        UUID(payload["jti"])
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidTokenError(
            "Token contains invalid identifiers",
        ) from exc

    return user_id


def create_refresh_token(
    *,
    user_id: UUID,
    session_id: UUID,
    expires_at: datetime,
) -> str:
    issued_at = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
        "token_type": "refresh",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def hash_refresh_token(
    token: str,
) -> str:
    return sha256(
        token.encode("utf-8"),
    ).hexdigest()


def decode_refresh_token(
    token: str,
) -> RefreshTokenClaims:
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": [
                "sub",
                "sid",
                "iat",
                "exp",
                "jti",
                "token_type",
            ],
        },
    )

    if payload["token_type"] != "refresh":
        raise InvalidTokenError(
            "Token is not a refresh token",
        )

    try:
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
        UUID(payload["jti"])
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidTokenError(
            "Token contains invalid identifiers",
        ) from exc

    return RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
    )