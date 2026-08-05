from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from core.security import (
    decode_refresh_token,
    hash_refresh_token,
    verify_password,
)
from models.refresh_sessions import RefreshSession
from models.users import User
from settings import settings


def register_alice(
    client: TestClient,
    *,
    password: str = "correct-horse-battery-staple",
) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_register_user_stores_password_hash(
    client: TestClient,
    read_stored_user: Callable[[UUID], User | None],
) -> None:
    plain_password = "correct-horse-battery-staple"

    response = client.post(
        "/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": plain_password,
        },
    )

    assert response.status_code == 201

    response_data = response.json()
    user_id = UUID(response_data["id"])

    assert response_data == {
        "id": str(user_id),
        "name": "Alice",
        "email": "alice@example.com",
    }
    assert "password" not in response_data
    assert "password_hash" not in response_data
    assert response.headers["Location"] == f"/users/{user_id}"

    stored_user = read_stored_user(user_id)

    assert stored_user is not None
    assert stored_user.password_hash is not None
    assert stored_user.password_hash != plain_password
    assert stored_user.password_hash.startswith("$argon2id$")
    assert verify_password(
        plain_password,
        stored_user.password_hash,
    )


def test_register_existing_email_returns_conflict(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "first-secure-password",
        },
    )

    second_response = client.post(
        "/auth/register",
        json={
            "name": "Another Alice",
            "email": "ALICE@example.com",
            "password": "second-secure-password",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "code": "user_email_already_exists",
        "message": "A user with this email already exists",
    }


def test_register_rejects_invalid_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "name": "   ",
            "email": "not-an-email",
            "password": "short",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 422


def test_login_returns_token_that_authenticates_user(
    client: TestClient,
    read_stored_refresh_session: Callable[
        [UUID],
        RefreshSession | None,
    ],
) -> None:
    password = "correct-horse-battery-staple"
    registered_user = register_alice(
        client,
        password=password,
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "  ALICE@example.com  ",
            "password": password,
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert login_data["token_type"] == "bearer"
    assert isinstance(login_data["access_token"], str)
    assert login_data["access_token"]
    assert "refresh_token" not in login_data

    refresh_token = login_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert refresh_token is not None

    set_cookie = login_response.headers["set-cookie"]

    assert "HttpOnly" in set_cookie
    assert "Path=/auth" in set_cookie
    assert "SameSite=lax" in set_cookie

    claims = decode_refresh_token(refresh_token)
    stored_session = read_stored_refresh_session(
        claims.session_id,
    )

    assert claims.user_id == UUID(registered_user["id"])
    assert stored_session is not None
    assert stored_session.user_id == claims.user_id
    assert stored_session.token_hash == hash_refresh_token(
        refresh_token,
    )
    assert stored_session.token_hash != refresh_token
    assert stored_session.revoked_at is None

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                f"Bearer {login_data['access_token']}"
            ),
        },
    )

    assert me_response.status_code == 200
    assert me_response.json() == registered_user


def test_login_rejects_wrong_password(
    client: TestClient,
) -> None:
    register_alice(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication credentials are invalid",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_login_rejects_unknown_email_with_same_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication credentials are invalid",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_refresh_rotates_both_tokens_and_stored_hash(
    client: TestClient,
    read_stored_refresh_session: Callable[
        [UUID],
        RefreshSession | None,
    ],
) -> None:
    password = "correct-horse-battery-staple"
    register_alice(client, password=password)
    login_response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": password,
        },
    )
    old_access_token = login_response.json()["access_token"]
    old_refresh_token = login_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert old_refresh_token is not None

    old_claims = decode_refresh_token(old_refresh_token)
    refresh_response = client.post("/auth/refresh")

    assert refresh_response.status_code == 200

    new_access_token = refresh_response.json()["access_token"]
    new_refresh_token = refresh_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert refresh_response.json()["token_type"] == "bearer"
    assert new_access_token != old_access_token
    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token

    new_claims = decode_refresh_token(new_refresh_token)

    assert new_claims.user_id == old_claims.user_id
    assert new_claims.session_id == old_claims.session_id

    stored_session = read_stored_refresh_session(
        new_claims.session_id,
    )

    assert stored_session is not None
    assert stored_session.token_hash == hash_refresh_token(
        new_refresh_token,
    )
    assert stored_session.token_hash != hash_refresh_token(
        old_refresh_token,
    )
    assert stored_session.revoked_at is None


def test_refresh_requires_cookie(
    client: TestClient,
) -> None:
    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication credentials are invalid",
    }


def test_reusing_rotated_refresh_token_revokes_session(
    client: TestClient,
    read_stored_refresh_session: Callable[
        [UUID],
        RefreshSession | None,
    ],
) -> None:
    password = "correct-horse-battery-staple"
    register_alice(client, password=password)
    login_response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": password,
        },
    )
    old_refresh_token = login_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert old_refresh_token is not None

    claims = decode_refresh_token(old_refresh_token)
    first_refresh_response = client.post("/auth/refresh")
    current_refresh_token = first_refresh_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert first_refresh_response.status_code == 200
    assert current_refresh_token is not None

    client.cookies.clear()
    client.cookies.set(
        settings.refresh_cookie_name,
        old_refresh_token,
        path="/auth",
    )
    reuse_response = client.post("/auth/refresh")

    assert reuse_response.status_code == 401

    stored_session = read_stored_refresh_session(
        claims.session_id,
    )

    assert stored_session is not None
    assert stored_session.revoked_at is not None

    client.cookies.clear()
    client.cookies.set(
        settings.refresh_cookie_name,
        current_refresh_token,
        path="/auth",
    )
    current_token_response = client.post("/auth/refresh")

    assert current_token_response.status_code == 401


def test_logout_revokes_session_and_deletes_cookie(
    client: TestClient,
    read_stored_refresh_session: Callable[
        [UUID],
        RefreshSession | None,
    ],
) -> None:
    password = "correct-horse-battery-staple"
    registered_user = register_alice(
        client,
        password=password,
    )
    login_response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": password,
        },
    )
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.cookies.get(
        settings.refresh_cookie_name,
    )

    assert refresh_token is not None

    claims = decode_refresh_token(refresh_token)
    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 204
    assert logout_response.content == b""

    set_cookie = logout_response.headers["set-cookie"]

    assert f"{settings.refresh_cookie_name}=\"\"" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/auth" in set_cookie
    assert client.cookies.get(
        settings.refresh_cookie_name,
    ) is None

    stored_session = read_stored_refresh_session(
        claims.session_id,
    )

    assert stored_session is not None
    assert stored_session.revoked_at is not None

    client.cookies.set(
        settings.refresh_cookie_name,
        refresh_token,
        path="/auth",
    )
    refresh_response = client.post("/auth/refresh")

    assert refresh_response.status_code == 401

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json() == registered_user


def test_logout_without_cookie_is_idempotent(
    client: TestClient,
) -> None:
    first_response = client.post("/auth/logout")
    second_response = client.post("/auth/logout")

    assert first_response.status_code == 204
    assert second_response.status_code == 204
