import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
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
from core.enums import OrganizationRole
from main import app
from models.base import Base
from models.contacts import Contact
from models.conversations import Conversation
from models.messages import Message
from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.refresh_sessions import RefreshSession
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
            text(f'CREATE SCHEMA "{TEST_SCHEMA}"'),
        )

    async with test_engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all,
        )


async def drop_test_schema() -> None:
    async with admin_engine.begin() as connection:
        await connection.execute(
            text(
                f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE',
            ),
        )

    await test_engine.dispose()
    await admin_engine.dispose()


async def clear_database() -> None:
    async with test_engine.begin() as connection:
        await connection.execute(
            delete(Message),
        )
        await connection.execute(
            delete(Conversation),
        )
        await connection.execute(
            delete(Contact),
        )
        await connection.execute(
            delete(OrganizationMember),
        )
        await connection.execute(
            delete(Organization),
        )
        await connection.execute(
            delete(RefreshSession),
        )
        await connection.execute(
            delete(User),
        )


async def find_stored_user(
    user_id: UUID,
) -> User | None:
    async with session_factory_for_tests() as session:
        return await session.get(
            User,
            user_id,
        )


async def find_stored_refresh_session(
    session_id: UUID,
) -> RefreshSession | None:
    async with session_factory_for_tests() as session:
        return await session.get(
            RefreshSession,
            session_id,
        )


async def find_stored_organization(
    organization_id: UUID,
) -> Organization | None:
    async with session_factory_for_tests() as session:
        return await session.get(
            Organization,
            organization_id,
        )


async def find_stored_membership(
    organization_id: UUID,
    user_id: UUID,
) -> OrganizationMember | None:
    async with session_factory_for_tests() as session:
        return await session.get(
            OrganizationMember,
            (
                organization_id,
                user_id,
            ),
        )


async def insert_stored_membership(
    organization_id: UUID,
    user_id: UUID,
    role: OrganizationRole,
) -> None:
    async with session_factory_for_tests() as session:
        session.add(
            OrganizationMember(
                organization_id=organization_id,
                user_id=user_id,
                role=role,
            ),
        )
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Iterator[None]:
    asyncio.run(create_test_schema())

    app.dependency_overrides[get_session] = (
        get_test_session
    )

    yield

    app.dependency_overrides.clear()
    asyncio.run(drop_test_schema())


@pytest.fixture(autouse=True)
def clean_database(
    test_database: None,
) -> Iterator[None]:
    asyncio.run(clear_database())

    yield

    asyncio.run(clear_database())


@pytest.fixture(scope="session")
def client(
    test_database: None,
) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_client_cookies(
    client: TestClient,
) -> Iterator[None]:
    client.cookies.clear()

    yield

    client.cookies.clear()


@pytest.fixture
def read_stored_user(
    test_database: None,
) -> Callable[[UUID], User | None]:
    def read(user_id: UUID) -> User | None:
        return asyncio.run(
            find_stored_user(user_id),
        )

    return read


@pytest.fixture
def read_stored_refresh_session(
    test_database: None,
) -> Callable[[UUID], RefreshSession | None]:
    def read(
        session_id: UUID,
    ) -> RefreshSession | None:
        return asyncio.run(
            find_stored_refresh_session(session_id),
        )

    return read


@pytest.fixture
def read_stored_organization(
    test_database: None,
) -> Callable[[UUID], Organization | None]:
    def read(
        organization_id: UUID,
    ) -> Organization | None:
        return asyncio.run(
            find_stored_organization(organization_id),
        )

    return read


@pytest.fixture
def read_stored_membership(
    test_database: None,
) -> Callable[[UUID, UUID], OrganizationMember | None]:
    def read(
        organization_id: UUID,
        user_id: UUID,
    ) -> OrganizationMember | None:
        return asyncio.run(
            find_stored_membership(
                organization_id,
                user_id,
            ),
        )

    return read


@pytest.fixture
def create_stored_membership(
    test_database: None,
) -> Callable[[UUID, UUID, OrganizationRole], None]:
    def create(
        organization_id: UUID,
        user_id: UUID,
        role: OrganizationRole,
    ) -> None:
        asyncio.run(
            insert_stored_membership(
                organization_id,
                user_id,
                role,
            ),
        )

    return create
