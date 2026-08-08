from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

import main
from models.users import User

TEST_PASSWORD = "correct-horse-battery-staple"


def register_user(
    client: TestClient,
    *,
    name: str,
    email: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


def authorization_headers(
    client: TestClient,
    email: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Process-Time" in response.headers


class UnavailableRedis:
    async def ping(self) -> None:
        raise RedisError("Redis is unavailable")


class UnavailableDatabase:
    def connect(self) -> None:
        raise SQLAlchemyError("PostgreSQL is unavailable")


def test_readiness_check_reports_dependency_failures(
    client: TestClient,
    monkeypatch,
) -> None:
    ready_response = client.get("/ready")

    assert ready_response.status_code == 200
    assert ready_response.json() == {"status": "ready"}

    original_redis = client.app.state.redis
    client.app.state.redis = UnavailableRedis()

    try:
        redis_down_response = client.get("/ready")
    finally:
        client.app.state.redis = original_redis

    assert redis_down_response.status_code == 503
    assert redis_down_response.json() == {"status": "not_ready"}

    monkeypatch.setattr(main, "engine", UnavailableDatabase())

    database_down_response = client.get("/ready")

    assert database_down_response.status_code == 503
    assert database_down_response.json() == {"status": "not_ready"}


def test_openapi_documents_redis_failure_responses(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    login_responses = schema["paths"]["/auth/login"]["post"][
        "responses"
    ]
    readiness_responses = schema["paths"]["/ready"]["get"][
        "responses"
    ]

    assert login_responses["429"]["headers"]["Retry-After"][
        "schema"
    ] == {"type": "integer"}
    assert readiness_responses["503"]["description"] == (
        "PostgreSQL or Redis is unavailable"
    )


def test_legacy_user_creation_is_disabled(
    client: TestClient,
) -> None:
    response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )

    assert response.status_code == 405


def test_user_endpoints_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/users").status_code == 401
    assert client.get(f"/users/{uuid4()}").status_code == 401


def test_user_can_only_read_self(client: TestClient) -> None:
    alice = register_user(
        client,
        name="Alice",
        email="alice@example.com",
    )
    bob = register_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    headers = authorization_headers(client, alice["email"])

    self_response = client.get(
        f"/users/{alice['id']}",
        headers=headers,
    )
    list_response = client.get("/users", headers=headers)
    other_response = client.get(
        f"/users/{bob['id']}",
        headers=headers,
    )
    other_update = client.patch(
        f"/users/{bob['id']}",
        headers=headers,
        json={"name": "Forged name"},
    )
    other_delete = client.delete(
        f"/users/{bob['id']}",
        headers=headers,
    )

    assert self_response.status_code == 200
    assert self_response.json() == alice
    assert list_response.status_code == 200
    assert list_response.json() == [alice]
    assert other_response.status_code == 404
    assert other_update.status_code == 404
    assert other_delete.status_code == 404


def test_user_lifecycle_is_self_only(
    client: TestClient,
    read_stored_user: Callable[[UUID], User | None],
) -> None:
    user = register_user(
        client,
        name="Alice",
        email="alice@example.com",
    )
    user_id = user["id"]
    headers = authorization_headers(client, user["email"])

    replace_response = client.put(
        f"/users/{user_id}",
        headers=headers,
        json={"name": "Bob", "email": "bob@example.com"},
    )
    assert replace_response.status_code == 200

    update_response = client.patch(
        f"/users/{user_id}",
        headers=headers,
        json={"name": "Charlie"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Charlie"

    delete_response = client.delete(
        f"/users/{user_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    assert client.get(
        f"/users/{user_id}",
        headers=headers,
    ).status_code == 401

    stored_user = read_stored_user(UUID(user_id))
    assert stored_user is not None
    assert stored_user.deleted_at is not None
    assert stored_user.name == "Charlie"
    assert stored_user.email == "bob@example.com"


def test_authenticated_user_id_validation(
    client: TestClient,
) -> None:
    user = register_user(
        client,
        name="Alice",
        email="alice@example.com",
    )
    headers = authorization_headers(client, user["email"])

    response = client.get("/users/not-a-uuid", headers=headers)

    assert response.status_code == 422
