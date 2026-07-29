from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main import app
from storage.users import users_by_id


@pytest.fixture
def client() -> Iterator[TestClient]:
    users_by_id.clear()

    with TestClient(app) as test_client:
        yield test_client

    users_by_id.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Process-Time" in response.headers


def test_create_and_get_user(client: TestClient) -> None:
    create_response = client.post(
        "/users",
        json={
            "name": "Alice",
            "email": "alice@example.com",
        },
    )

    assert create_response.status_code == 201

    created_user = create_response.json()
    user_id = UUID(created_user["id"])

    assert created_user == {
        "id": str(user_id),
        "name": "Alice",
        "email": "alice@example.com",
    }
    assert create_response.headers["Location"] == f"/users/{user_id}"

    get_response = client.get(f"/users/{user_id}")

    assert get_response.status_code == 200
    assert get_response.json() == created_user


def test_create_user_with_existing_email_returns_conflict(
    client: TestClient,
) -> None:
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
    }

    first_response = client.post(
        "/users",
        json=user_data,
    )
    second_response = client.post(
        "/users",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "code": "user_email_already_exists",
        "message": "A user with this email already exists",
    }


def test_get_missing_user_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/users/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "user_not_found",
        "message": "User not found",
    }


def test_create_user_rejects_invalid_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/users",
        json={
            "name": "   ",
            "email": "not-an-email",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_user_lifecycle(client: TestClient) -> None:
    create_response = client.post(
        "/users",
        json={
            "name": "Alice",
            "email": "alice@example.com",
        },
    )

    assert create_response.status_code == 201

    user_id = create_response.json()["id"]

    replace_response = client.put(
        f"/users/{user_id}",
        json={
            "name": "Bob",
            "email": "bob@example.com",
        },
    )

    assert replace_response.status_code == 200
    assert replace_response.json() == {
        "id": user_id,
        "name": "Bob",
        "email": "bob@example.com",
    }

    update_response = client.patch(
        f"/users/{user_id}",
        json={
            "name": "Charlie",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": user_id,
        "name": "Charlie",
        "email": "bob@example.com",
    }

    delete_response = client.delete(f"/users/{user_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/users/{user_id}")

    assert get_response.status_code == 404