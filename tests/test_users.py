import asyncio
from collections.abc import AsyncIterator, Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from dependencies.database import get_session
from main import app
from models.base import Base
from models.users import User
from settings import settings


TEST_SCHEMA = f"test_{uuid4().hex}"

admin_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
)

test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={
        "server_settings": {
            "search_path": TEST_SCHEMA,
        },
    },
)

session_factory_for_tests = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with session_factory_for_tests() as session:
        yield session


async def create_test_schema() -> None:
    async with admin_engine.begin() as connection:
        await connection.execute(
            text(f'CREATE SCHEMA "{TEST_SCHEMA}"')
        )

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_test_schema() -> None:
    async with admin_engine.begin() as connection:
        await connection.execute(
            text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE')
        )

    await test_engine.dispose()
    await admin_engine.dispose()


async def clear_users() -> None:
    async with test_engine.begin() as connection:
        await connection.execute(delete(User))


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Iterator[None]:
    asyncio.run(create_test_schema())
    app.dependency_overrides[get_session] = get_test_session

    yield

    app.dependency_overrides.clear()
    asyncio.run(drop_test_schema())


@pytest.fixture(autouse=True)
def clean_database(test_database: None) -> Iterator[None]:
    asyncio.run(clear_users())

    yield

    asyncio.run(clear_users())


@pytest.fixture(scope="session")
def client(test_database: None) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


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
