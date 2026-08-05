from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_refresh_token,
)
from settings import settings


def make_token(
    *,
    user_id: UUID,
    expires_at: datetime,
    token_type: str = "access",
    include_exp: bool = True,
    secret: str | None = None,
) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "jti": str(uuid4()),
        "token_type": token_type,
    }

    if include_exp:
        payload["exp"] = expires_at

    return jwt.encode(
        payload,
        secret or settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def test_access_token_round_trip_returns_user_id() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)

    assert decode_access_token(token) == user_id


def test_access_token_with_wrong_signature_is_rejected() -> None:
    user_id = uuid4()
    token = make_token(
        user_id=user_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        secret="a-different-secret-that-is-long-enough",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_expired_access_token_is_rejected() -> None:
    user_id = uuid4()
    token = make_token(
        user_id=user_id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_refresh_token_is_rejected_as_access_token() -> None:
    user_id = uuid4()
    token = make_token(
        user_id=user_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        token_type="refresh",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_access_token_without_required_claim_is_rejected() -> None:
    user_id = uuid4()
    token = make_token(
        user_id=user_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        include_exp=False,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_refresh_token_round_trip_returns_claims() -> None:
    user_id = uuid4()
    session_id = uuid4()
    token = create_refresh_token(
        user_id=user_id,
        session_id=session_id,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    claims = decode_refresh_token(token)

    assert claims.user_id == user_id
    assert claims.session_id == session_id


def test_access_token_is_rejected_as_refresh_token() -> None:
    token = create_access_token(uuid4())

    with pytest.raises(InvalidTokenError):
        decode_refresh_token(token)


def test_expired_refresh_token_is_rejected() -> None:
    token = create_refresh_token(
        user_id=uuid4(),
        session_id=uuid4(),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(InvalidTokenError):
        decode_refresh_token(token)


def test_refresh_token_hash_is_stable_and_fixed_length() -> None:
    token = create_refresh_token(
        user_id=uuid4(),
        session_id=uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    first_hash = hash_refresh_token(token)
    second_hash = hash_refresh_token(token)

    assert first_hash == second_hash
    assert len(first_hash) == 64
    assert first_hash != token
