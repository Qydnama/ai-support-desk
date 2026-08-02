from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from models.users import User


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


def test_list_users(client: TestClient) -> None:
    first_user = client.post(
        "/users",
        json={
            "name": "Alice",
            "email": "alice@example.com",
        },
    ).json()
    second_user = client.post(
        "/users",
        json={
            "name": "Bob",
            "email": "bob@example.com",
        },
    ).json()

    response = client.get("/users")

    assert response.status_code == 200
    assert {user["id"] for user in response.json()} == {
        first_user["id"],
        second_user["id"],
    }


def test_create_user_with_existing_email_returns_conflict(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/users",
        json={
            "name": "Alice",
            "email": "alice@example.com",
        },
    )
    second_response = client.post(
        "/users",
        json={
            "name": "Another Alice",
            "email": "ALICE@example.com",
        },
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


def test_get_user_rejects_invalid_uuid(client: TestClient) -> None:
    response = client.get("/users/not-a-uuid")

    assert response.status_code == 422


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


def test_user_lifecycle(
    client: TestClient,
    read_stored_user: Callable[[UUID], User | None],
) -> None:
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

    list_response = client.get("/users")

    assert list_response.status_code == 200
    assert list_response.json() == []

    stored_user = read_stored_user(
        UUID(user_id),
    )

    assert stored_user is not None
    assert stored_user.deleted_at is not None
    assert stored_user.name == "Charlie"
    assert stored_user.email == "bob@example.com"
