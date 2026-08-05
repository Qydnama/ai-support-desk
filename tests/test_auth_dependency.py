from uuid import UUID, uuid4

from fastapi import status
from fastapi.testclient import TestClient

from core.security import create_access_token


def assert_authentication_required(response_status: int) -> None:
    assert response_status == status.HTTP_401_UNAUTHORIZED


def test_current_user_requires_bearer_token(
    client: TestClient,
) -> None:
    response = client.get("/auth/me")

    assert_authentication_required(response.status_code)
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication credentials are invalid",
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_current_user_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer not-a-jwt",
        },
    )

    assert_authentication_required(response.status_code)
    assert response.json()["code"] == "authentication_required"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_current_user_rejects_unknown_user(
    client: TestClient,
) -> None:
    token = create_access_token(uuid4())

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert_authentication_required(response.status_code)


def test_current_user_returns_authenticated_user(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    user_data = register_response.json()
    token = create_access_token(UUID(user_data["id"]))

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert register_response.status_code == status.HTTP_201_CREATED
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user_data
