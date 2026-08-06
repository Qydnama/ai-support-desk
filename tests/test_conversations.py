import asyncio
from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
from asyncpg.exceptions import DeadlockDetectedError
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import MessageSenderType, OrganizationRole
from models.conversations import Conversation
from models.idempotency_records import IdempotencyRecord
from models.messages import Message
from models.users import User
from repositories import conversations as conversation_repository
from repositories import idempotency_records as idempotency_repository
from schemas.messages import MessageCreate
from services import messages as message_service

TEST_PASSWORD = "correct-horse-battery-staple"


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

def create_user(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "name": f"User {suffix}",
            "email": f"{suffix}@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_organization(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    email = f"owner-{suffix}@example.com"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Owner {suffix}",
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert register_response.status_code == 201
    response = client.post(
        "/organizations",
        headers=authorization_headers(client, email),
        json={
            "name": f"Organization {suffix}",
            "slug": f"organization-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_contact(
    client: TestClient,
    organization_id: str,
    suffix: str,
    headers: dict[str, str],
) -> dict[str, str]:
    response = client.post(
        f"/organizations/{organization_id}/contacts",
        headers=headers,
        json={
            "name": f"Customer {suffix}",
            "email": f"customer-{suffix}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(
    client: TestClient,
    organization_id: str,
    contact_id: str,
    subject: str,
    headers: dict[str, str],
) -> dict[str, str]:
    response = client.post(
        "/conversations",
        headers=headers,
        json={
            "organization_id": organization_id,
            "contact_id": contact_id,
            "subject": subject,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_support_conversation_lifecycle(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    agent = create_user(client, "support-agent")
    organization = create_organization(client, "support-lifecycle")
    create_stored_membership(
        UUID(organization["id"]),
        UUID(agent["id"]),
        OrganizationRole.AGENT,
    )
    agent_headers = authorization_headers(
        client,
        agent["email"],
    )
    contact = create_contact(
        client,
        organization["id"],
        "alice",
        agent_headers,
    )

    create_response = client.post(
        "/conversations",
        headers=agent_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Cannot reset password",
        },
    )
    assert create_response.status_code == 201
    conversation = create_response.json()
    conversation_id = conversation["id"]
    assert conversation["status"] == "OPEN"
    assert conversation["version"] == 1
    assert conversation["contact_id"] == contact["id"]
    assert conversation["assigned_user_id"] is None

    claim_response = client.post(
        f"/conversations/{conversation_id}/claim",
        headers=agent_headers,
    )
    assert claim_response.status_code == 200
    assert claim_response.json()["assigned_user_id"] == agent["id"]
    assert claim_response.json()["version"] == 2

    update_response = client.patch(
        f"/conversations/{conversation_id}",
        headers=agent_headers,
        json={
            "status": "PENDING",
            "expected_version": claim_response.json()["version"],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "PENDING"
    assert update_response.json()["assigned_user_id"] == agent["id"]
    assert update_response.json()["version"] == 3

    contact_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **agent_headers,
            "Idempotency-Key": "support-contact-message",
        },
        json={
            "sender_type": "CONTACT",
            "author_contact_id": contact["id"],
            "content": "The reset email never arrives.",
        },
    )
    assert contact_message.status_code == 201

    agent_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **agent_headers,
            "Idempotency-Key": "support-agent-message",
        },
        json={
            "sender_type": "AGENT",
            "content": "I will check your account.",
        },
    )
    assert agent_message.status_code == 201

    ai_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **agent_headers,
            "Idempotency-Key": "support-ai-message",
        },
        json={
            "sender_type": "AI",
            "content": "I found an account recovery article.",
        },
    )
    assert ai_message.status_code == 201

    messages_response = client.get(
        f"/conversations/{conversation_id}/messages",
        headers=agent_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["sender_type"] for message in messages] == [
        "CONTACT",
        "AGENT",
        "AI",
    ]
    assert messages[0]["author_contact_id"] == contact["id"]
    assert messages[1]["author_user_id"] == agent["id"]
    assert messages[2]["author_user_id"] is None
    assert messages[2]["author_contact_id"] is None


def test_claim_conversation_and_reject_repeated_claim(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    agent = create_user(client, "claim-agent")
    organization = create_organization(client, "claim")
    create_stored_membership(
        UUID(organization["id"]),
        UUID(agent["id"]),
        OrganizationRole.AGENT,
    )
    agent_headers = authorization_headers(
        client,
        agent["email"],
    )
    contact = create_contact(
        client,
        organization["id"],
        "claim",
        agent_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=agent_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Claim this conversation",
        },
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    claim_response = client.post(
        f"/conversations/{conversation_id}/claim",
        headers=agent_headers,
    )

    assert claim_response.status_code == 200
    assert claim_response.json()["assigned_user_id"] == agent["id"]
    assert claim_response.json()["version"] == 2

    repeated_claim_response = client.post(
        f"/conversations/{conversation_id}/claim",
        headers=agent_headers,
    )

    assert repeated_claim_response.status_code == 409
    assert repeated_claim_response.json() == {
        "code": "conversation_already_assigned",
        "message": "Conversation is already assigned",
    }

    stored_response = client.get(
        f"/conversations/{conversation_id}",
        headers=agent_headers,
    )
    assert stored_response.status_code == 200
    assert stored_response.json()["assigned_user_id"] == agent["id"]


def test_conversation_patch_rejects_assignee_forgery(
    client: TestClient,
) -> None:
    organization = create_organization(client, "patch-assignee")
    owner_headers = authorization_headers(
        client,
        "owner-patch-assignee@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "patch-assignee",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Cannot forge assignee",
        },
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    forged_patch_response = client.patch(
        f"/conversations/{conversation_id}",
        headers=owner_headers,
        json={"assigned_user_id": str(uuid4())},
    )

    assert forged_patch_response.status_code == 422

    stored_response = client.get(
        f"/conversations/{conversation_id}",
        headers=owner_headers,
    )
    assert stored_response.status_code == 200
    assert stored_response.json()["assigned_user_id"] is None


def test_conversation_update_detects_optimistic_version_conflict(
    client: TestClient,
) -> None:
    organization = create_organization(client, "version-conflict")
    owner_headers = authorization_headers(
        client,
        "owner-version-conflict@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "version-conflict",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Detect stale update",
        },
    )
    assert create_response.status_code == 201
    conversation = create_response.json()
    assert conversation["version"] == 1

    first_update_response = client.patch(
        f"/conversations/{conversation['id']}",
        headers=owner_headers,
        json={
            "status": "PENDING",
            "expected_version": 1,
        },
    )
    assert first_update_response.status_code == 200
    assert first_update_response.json()["status"] == "PENDING"
    assert first_update_response.json()["version"] == 2

    stale_update_response = client.patch(
        f"/conversations/{conversation['id']}",
        headers=owner_headers,
        json={
            "status": "RESOLVED",
            "expected_version": 1,
        },
    )
    assert stale_update_response.status_code == 409
    assert stale_update_response.json() == {
        "code": "conversation_version_conflict",
        "message": "Conversation was modified by another request",
    }

    stored_response = client.get(
        f"/conversations/{conversation['id']}",
        headers=owner_headers,
    )
    assert stored_response.status_code == 200
    assert stored_response.json()["status"] == "PENDING"
    assert stored_response.json()["version"] == 2


def test_concurrent_claim_has_exactly_one_winner(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_agent = create_user(client, "claim-first-agent")
    second_agent = create_user(client, "claim-second-agent")
    organization = create_organization(client, "concurrent-claim")
    organization_id = UUID(organization["id"])

    for agent in (first_agent, second_agent):
        create_stored_membership(
            organization_id,
            UUID(agent["id"]),
            OrganizationRole.AGENT,
        )

    owner_headers = authorization_headers(
        client,
        "owner-concurrent-claim@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "concurrent-claim",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Only one agent may claim this",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def run_concurrent_claims() -> tuple[list[UUID | None], UUID]:
        barrier = asyncio.Barrier(2)

        async def claim(user_id: UUID) -> UUID | None:
            async with concurrent_session_factory() as session:
                await barrier.wait()
                conversation = (
                    await conversation_repository.claim_if_unassigned(
                        session=session,
                        conversation_id=conversation_id,
                        organization_id=organization_id,
                        user_id=user_id,
                    )
                )

                if conversation is None:
                    await session.rollback()
                    return None

                await session.commit()
                return user_id

        results = await asyncio.gather(
            claim(UUID(first_agent["id"])),
            claim(UUID(second_agent["id"])),
        )

        async with concurrent_session_factory() as verification_session:
            stored_conversation = await verification_session.get(
                Conversation,
                conversation_id,
            )

        assert stored_conversation is not None
        assert stored_conversation.assigned_user_id is not None

        return results, stored_conversation.assigned_user_id

    results, assigned_user_id = asyncio.run(run_concurrent_claims())
    winners = [result for result in results if result is not None]

    assert len(winners) == 1
    assert assigned_user_id == winners[0]


def test_read_committed_allows_non_repeatable_read(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    agent = create_user(client, "isolation-agent")
    organization = create_organization(client, "isolation")
    organization_id = UUID(organization["id"])
    agent_id = UUID(agent["id"])
    create_stored_membership(
        organization_id,
        agent_id,
        OrganizationRole.AGENT,
    )
    agent_headers = authorization_headers(
        client,
        agent["email"],
    )
    contact = create_contact(
        client,
        organization["id"],
        "isolation",
        agent_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=agent_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Observe READ COMMITTED",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def observe_committed_claim() -> tuple[
        str,
        UUID | None,
        UUID | None,
    ]:
        async with (
            concurrent_session_factory() as observer,
            concurrent_session_factory() as writer,
        ):
            isolation_level = await observer.scalar(
                text("SHOW transaction_isolation"),
            )
            before_claim = await observer.scalar(
                select(Conversation.assigned_user_id).where(
                    Conversation.id == conversation_id,
                ),
            )

            claimed_conversation = (
                await conversation_repository.claim_if_unassigned(
                    session=writer,
                    conversation_id=conversation_id,
                    organization_id=organization_id,
                    user_id=agent_id,
                )
            )
            assert claimed_conversation is not None
            await writer.commit()

            after_claim = await observer.scalar(
                select(Conversation.assigned_user_id).where(
                    Conversation.id == conversation_id,
                ),
            )
            await observer.rollback()

        assert isolation_level is not None

        return isolation_level, before_claim, after_claim

    isolation_level, before_claim, after_claim = asyncio.run(
        observe_committed_claim(),
    )

    assert isolation_level == "read committed"
    assert before_claim is None
    assert after_claim == agent_id


def test_postgresql_prevents_dirty_read(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    agent = create_user(client, "dirty-read-agent")
    organization = create_organization(client, "dirty-read")
    organization_id = UUID(organization["id"])
    agent_id = UUID(agent["id"])
    create_stored_membership(
        organization_id,
        agent_id,
        OrganizationRole.AGENT,
    )
    agent_headers = authorization_headers(
        client,
        agent["email"],
    )
    contact = create_contact(
        client,
        organization["id"],
        "dirty-read",
        agent_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=agent_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Dirty read must be impossible",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def observe_uncommitted_update() -> tuple[
        UUID | None,
        UUID | None,
    ]:
        async with (
            concurrent_session_factory() as writer,
            concurrent_session_factory() as observer,
        ):
            conversation = await writer.get(
                Conversation,
                conversation_id,
            )
            assert conversation is not None

            conversation.assigned_user_id = agent_id
            await writer.flush()

            value_during_uncommitted_update = await observer.scalar(
                select(Conversation.assigned_user_id).where(
                    Conversation.id == conversation_id,
                ),
            )

            await writer.rollback()

            value_after_rollback = await observer.scalar(
                select(Conversation.assigned_user_id).where(
                    Conversation.id == conversation_id,
                ),
            )
            await observer.rollback()

        return value_during_uncommitted_update, value_after_rollback

    value_during_update, value_after_rollback = asyncio.run(
        observe_uncommitted_update(),
    )

    assert value_during_update is None
    assert value_after_rollback is None


def test_naive_claim_demonstrates_lost_update(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_agent = create_user(client, "lost-update-first")
    second_agent = create_user(client, "lost-update-second")
    organization = create_organization(client, "lost-update")
    organization_id = UUID(organization["id"])
    first_agent_id = UUID(first_agent["id"])
    second_agent_id = UUID(second_agent["id"])

    for agent_id in (first_agent_id, second_agent_id):
        create_stored_membership(
            organization_id,
            agent_id,
            OrganizationRole.AGENT,
        )

    owner_headers = authorization_headers(
        client,
        "owner-lost-update@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "lost-update",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Demonstrate lost update",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def demonstrate_lost_update() -> tuple[list[UUID], UUID]:
        both_have_read_null = asyncio.Barrier(2)
        first_commit_finished = asyncio.Event()

        async def naive_claim(
            user_id: UUID,
            *,
            wait_for_first_commit: bool,
        ) -> UUID:
            async with concurrent_session_factory() as session:
                conversation = await session.get(
                    Conversation,
                    conversation_id,
                )
                assert conversation is not None
                assert conversation.assigned_user_id is None

                await both_have_read_null.wait()

                if wait_for_first_commit:
                    await first_commit_finished.wait()

                conversation.assigned_user_id = user_id
                await session.commit()

                if not wait_for_first_commit:
                    first_commit_finished.set()

                return user_id

        reported_successes = await asyncio.gather(
            naive_claim(
                first_agent_id,
                wait_for_first_commit=False,
            ),
            naive_claim(
                second_agent_id,
                wait_for_first_commit=True,
            ),
        )

        async with concurrent_session_factory() as verification_session:
            stored_conversation = await verification_session.get(
                Conversation,
                conversation_id,
            )

        assert stored_conversation is not None
        assert stored_conversation.assigned_user_id is not None

        return reported_successes, stored_conversation.assigned_user_id

    reported_successes, final_assignee_id = asyncio.run(
        demonstrate_lost_update(),
    )

    assert reported_successes == [first_agent_id, second_agent_id]
    assert final_assignee_id == second_agent_id
    assert final_assignee_id != first_agent_id


def test_deadlock_and_stable_lock_order(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = create_organization(client, "deadlock")
    owner_headers = authorization_headers(
        client,
        "owner-deadlock@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "deadlock",
        owner_headers,
    )
    conversation_ids: list[UUID] = []

    for subject in ("Deadlock first row", "Deadlock second row"):
        response = client.post(
            "/conversations",
            headers=owner_headers,
            json={
                "organization_id": organization["id"],
                "contact_id": contact["id"],
                "subject": subject,
            },
        )
        assert response.status_code == 201
        conversation_ids.append(UUID(response.json()["id"]))

    async def lock_conversation(
        session: AsyncSession,
        conversation_id: UUID,
    ) -> None:
        statement = (
            select(Conversation.id)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )
        locked_id = await session.scalar(statement)
        assert locked_id == conversation_id

    async def reproduce_deadlock() -> list[str]:
        first_rows_locked = asyncio.Barrier(2)

        async def lock_in_opposite_order(
            first_id: UUID,
            second_id: UUID,
        ) -> str:
            async with concurrent_session_factory() as session:
                try:
                    await lock_conversation(session, first_id)
                    await first_rows_locked.wait()
                    await lock_conversation(session, second_id)
                    await session.commit()
                except DBAPIError as exc:
                    await session.rollback()
                    postgres_error = exc.orig.__cause__

                    if isinstance(
                        postgres_error,
                        DeadlockDetectedError,
                    ):
                        return "deadlock"

                    raise

            return "committed"

        return await asyncio.wait_for(
            asyncio.gather(
                lock_in_opposite_order(
                    conversation_ids[0],
                    conversation_ids[1],
                ),
                lock_in_opposite_order(
                    conversation_ids[1],
                    conversation_ids[0],
                ),
            ),
            timeout=10,
        )

    async def use_stable_lock_order() -> list[str]:
        start_together = asyncio.Barrier(2)
        ordered_ids = sorted(conversation_ids)

        async def lock_in_same_order() -> str:
            async with concurrent_session_factory() as session:
                await start_together.wait()

                for conversation_id in ordered_ids:
                    await lock_conversation(session, conversation_id)

                await session.commit()

            return "committed"

        return await asyncio.wait_for(
            asyncio.gather(
                lock_in_same_order(),
                lock_in_same_order(),
            ),
            timeout=10,
        )

    deadlock_results = asyncio.run(reproduce_deadlock())
    ordered_results = asyncio.run(use_stable_lock_order())

    assert sorted(deadlock_results) == ["committed", "deadlock"]
    assert ordered_results == ["committed", "committed"]


def test_select_for_update_serializes_claim_decision(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_agent = create_user(client, "row-lock-first")
    second_agent = create_user(client, "row-lock-second")
    organization = create_organization(client, "row-lock")
    organization_id = UUID(organization["id"])
    first_agent_id = UUID(first_agent["id"])
    second_agent_id = UUID(second_agent["id"])

    for agent_id in (first_agent_id, second_agent_id):
        create_stored_membership(
            organization_id,
            agent_id,
            OrganizationRole.AGENT,
        )

    owner_headers = authorization_headers(
        client,
        "owner-row-lock@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "row-lock",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Serialize claim with a row lock",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def demonstrate_row_lock() -> tuple[
        UUID,
        UUID | None,
        str,
    ]:
        first_has_lock = asyncio.Event()
        second_is_waiting_for_lock = asyncio.Event()
        second_backend_pid: asyncio.Future[int] = (
            asyncio.get_running_loop().create_future()
        )

        lock_statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )

        async def first_claim() -> UUID:
            async with concurrent_session_factory() as session:
                conversation = await session.scalar(lock_statement)
                assert conversation is not None
                assert conversation.assigned_user_id is None
                first_has_lock.set()

                await second_is_waiting_for_lock.wait()

                conversation.assigned_user_id = first_agent_id
                await session.commit()

            return first_agent_id

        async def second_claim() -> UUID | None:
            await first_has_lock.wait()

            async with concurrent_session_factory() as session:
                backend_pid = await session.scalar(
                    text("SELECT pg_backend_pid()"),
                )
                assert backend_pid is not None
                second_backend_pid.set_result(backend_pid)

                conversation = await session.scalar(lock_statement)
                assert conversation is not None
                assert conversation.assigned_user_id == first_agent_id

                await session.rollback()

            return None

        async def observe_lock_wait() -> str:
            backend_pid = await second_backend_pid

            async with concurrent_session_factory() as session:
                for _ in range(200):
                    result = await session.execute(
                        text(
                            "SELECT wait_event_type, wait_event "
                            "FROM pg_stat_activity "
                            "WHERE pid = :backend_pid"
                        ),
                        {"backend_pid": backend_pid},
                    )
                    row = result.one()

                    if row.wait_event_type == "Lock":
                        second_is_waiting_for_lock.set()
                        await session.rollback()
                        return row.wait_event

                    await asyncio.sleep(0.01)

                await session.rollback()

            raise AssertionError(
                "The second transaction did not wait for a row lock",
            )

        first_result, second_result, wait_event = await asyncio.wait_for(
            asyncio.gather(
                first_claim(),
                second_claim(),
                observe_lock_wait(),
            ),
            timeout=10,
        )

        return first_result, second_result, wait_event

    first_result, second_result, wait_event = asyncio.run(
        demonstrate_row_lock(),
    )

    assert first_result == first_agent_id
    assert second_result is None
    assert wait_event == "transactionid"


def test_atomic_claim_waiter_succeeds_after_first_rollback(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_agent = create_user(client, "atomic-rollback-first")
    second_agent = create_user(client, "atomic-rollback-second")
    organization = create_organization(client, "atomic-rollback")
    organization_id = UUID(organization["id"])
    first_agent_id = UUID(first_agent["id"])
    second_agent_id = UUID(second_agent["id"])

    for agent_id in (first_agent_id, second_agent_id):
        create_stored_membership(
            organization_id,
            agent_id,
            OrganizationRole.AGENT,
        )

    owner_headers = authorization_headers(
        client,
        "owner-atomic-rollback@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "atomic-rollback",
        owner_headers,
    )
    create_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Second claim wins after rollback",
        },
    )
    assert create_response.status_code == 201
    conversation_id = UUID(create_response.json()["id"])

    async def demonstrate_rollback_handoff() -> tuple[
        UUID,
        UUID,
        str,
    ]:
        first_has_updated = asyncio.Event()
        second_is_waiting_for_lock = asyncio.Event()
        second_backend_pid: asyncio.Future[int] = (
            asyncio.get_running_loop().create_future()
        )

        async def first_claim_then_rollback() -> UUID:
            async with concurrent_session_factory() as session:
                claimed = (
                    await conversation_repository.claim_if_unassigned(
                        session=session,
                        conversation_id=conversation_id,
                        organization_id=organization_id,
                        user_id=first_agent_id,
                    )
                )
                assert claimed is not None
                first_has_updated.set()

                await second_is_waiting_for_lock.wait()
                await session.rollback()

            return first_agent_id

        async def second_claim_after_wait() -> UUID:
            await first_has_updated.wait()

            async with concurrent_session_factory() as session:
                backend_pid = await session.scalar(
                    text("SELECT pg_backend_pid()"),
                )
                assert backend_pid is not None
                second_backend_pid.set_result(backend_pid)

                claimed = (
                    await conversation_repository.claim_if_unassigned(
                        session=session,
                        conversation_id=conversation_id,
                        organization_id=organization_id,
                        user_id=second_agent_id,
                    )
                )
                assert claimed is not None
                assert claimed.assigned_user_id == second_agent_id
                await session.commit()

            return second_agent_id

        async def observe_lock_wait() -> str:
            backend_pid = await second_backend_pid

            async with concurrent_session_factory() as session:
                for _ in range(200):
                    result = await session.execute(
                        text(
                            "SELECT wait_event_type, wait_event "
                            "FROM pg_stat_activity "
                            "WHERE pid = :backend_pid"
                        ),
                        {"backend_pid": backend_pid},
                    )
                    row = result.one()

                    if row.wait_event_type == "Lock":
                        second_is_waiting_for_lock.set()
                        await session.rollback()
                        return row.wait_event

                    await asyncio.sleep(0.01)

                await session.rollback()

            raise AssertionError(
                "The second atomic update did not wait for a row lock",
            )

        first_result, second_result, wait_event = await asyncio.wait_for(
            asyncio.gather(
                first_claim_then_rollback(),
                second_claim_after_wait(),
                observe_lock_wait(),
            ),
            timeout=10,
        )

        return first_result, second_result, wait_event

    first_result, second_result, wait_event = asyncio.run(
        demonstrate_rollback_handoff(),
    )

    assert first_result == first_agent_id
    assert second_result == second_agent_id
    assert wait_event == "transactionid"

    stored_response = client.get(
        f"/conversations/{conversation_id}",
        headers=owner_headers,
    )
    assert stored_response.status_code == 200
    assert stored_response.json()["assigned_user_id"] == str(
        second_agent_id,
    )


def test_conversation_enforces_tenant_and_participants(
    client: TestClient,
) -> None:
    organization = create_organization(client, "tenant-a")
    other_organization = create_organization(client, "tenant-b")
    organization_headers = authorization_headers(
        client,
        "owner-tenant-a@example.com",
    )
    other_organization_headers = authorization_headers(
        client,
        "owner-tenant-b@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "tenant-a",
        organization_headers,
    )
    other_contact = create_contact(
        client,
        other_organization["id"],
        "tenant-b",
        other_organization_headers,
    )
    outsider = create_user(client, "outsider")

    wrong_tenant = client.post(
        "/conversations",
        headers=organization_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": other_contact["id"],
            "subject": "Wrong tenant",
        },
    )
    assert wrong_tenant.status_code == 404
    assert wrong_tenant.json()["code"] == "contact_not_found"

    conversation_response = client.post(
        "/conversations",
        headers=organization_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Correct tenant",
        },
    )
    conversation_id = conversation_response.json()["id"]

    unauthenticated_claim = client.post(
        f"/conversations/{conversation_id}/claim",
    )
    outsider_claim = client.post(
        f"/conversations/{conversation_id}/claim",
        headers=other_organization_headers,
    )

    assert unauthenticated_claim.status_code == 401
    assert outsider_claim.status_code == 404

    owner_conversation_response = client.get(
        f"/conversations/{conversation_id}",
        headers=organization_headers,
    )
    assert owner_conversation_response.status_code == 200
    assert owner_conversation_response.json()["assigned_user_id"] is None

    outsider_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **authorization_headers(
                client,
                outsider["email"],
            ),
            "Idempotency-Key": "outsider-message",
        },
        json={
            "sender_type": "AGENT",
            "content": "I am not an agent of this organization.",
        },
    )
    assert outsider_message.status_code == 404

    outsider_list = client.get(
        "/conversations",
        headers=authorization_headers(
            client,
            outsider["email"],
        ),
        params={"organization_id": organization["id"]},
    )
    assert outsider_list.status_code == 403
    assert outsider_list.json()["code"] == (
        "organization_member_required"
    )
    assert client.get(
        "/conversations",
        params={"organization_id": organization["id"]},
    ).status_code == 401

    wrong_contact_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **organization_headers,
            "Idempotency-Key": "wrong-contact-message",
        },
        json={
            "sender_type": "CONTACT",
            "author_contact_id": other_contact["id"],
            "content": "I do not own this conversation.",
        },
    )
    assert wrong_contact_message.status_code == 404

    invalid_author_shape = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **organization_headers,
            "Idempotency-Key": "invalid-author-message",
        },
        json={
            "sender_type": "AI",
            "author_contact_id": contact["id"],
            "content": "AI cannot have a contact author.",
        },
    )
    assert invalid_author_shape.status_code == 422

    forged_agent = client.post(
        f"/conversations/{conversation_id}/messages",
        headers={
            **organization_headers,
            "Idempotency-Key": "forged-agent-message",
        },
        json={
            "sender_type": "AGENT",
            "author_user_id": outsider["id"],
            "content": "Attempt to forge another agent.",
        },
    )
    assert forged_agent.status_code == 422


def test_message_idempotency_reuses_the_original_message(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = create_organization(client, "message-idempotency")
    owner_headers = authorization_headers(
        client,
        "owner-message-idempotency@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "message-idempotency",
        owner_headers,
    )
    conversation = create_conversation(
        client,
        organization["id"],
        contact["id"],
        "Do not duplicate this message",
        owner_headers,
    )
    request_headers = {
        **owner_headers,
        "Idempotency-Key": "same-command-key",
    }
    payload = {
        "sender_type": "AGENT",
        "content": "Send this only once.",
    }

    first_response = client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=request_headers,
        json=payload,
    )
    repeated_response = client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=request_headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert repeated_response.status_code == 201
    assert repeated_response.json() == first_response.json()
    assert repeated_response.headers["Location"] == (
        first_response.headers["Location"]
    )

    async def read_stored_result() -> tuple[int, int, UUID | None]:
        async with concurrent_session_factory() as session:
            message_count = await session.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == UUID(conversation["id"]),
                ),
            )
            record_count = await session.scalar(
                select(func.count(IdempotencyRecord.id)).where(
                    IdempotencyRecord.organization_id
                    == UUID(organization["id"]),
                    IdempotencyRecord.key == "same-command-key",
                ),
            )
            message_id = await session.scalar(
                select(IdempotencyRecord.message_id).where(
                    IdempotencyRecord.organization_id
                    == UUID(organization["id"]),
                    IdempotencyRecord.key == "same-command-key",
                ),
            )

        return message_count or 0, record_count or 0, message_id

    message_count, record_count, stored_message_id = asyncio.run(
        read_stored_result(),
    )

    assert message_count == 1
    assert record_count == 1
    assert stored_message_id == UUID(first_response.json()["id"])


def test_message_idempotency_rejects_changed_payload_and_accepts_new_key(
    client: TestClient,
) -> None:
    organization = create_organization(client, "message-key-contract")
    owner_headers = authorization_headers(
        client,
        "owner-message-key-contract@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "message-key-contract",
        owner_headers,
    )
    conversation = create_conversation(
        client,
        organization["id"],
        contact["id"],
        "Check idempotency key reuse",
        owner_headers,
    )
    endpoint = f"/conversations/{conversation['id']}/messages"
    original_payload = {
        "sender_type": "AGENT",
        "content": "Original message.",
    }

    first_response = client.post(
        endpoint,
        headers={
            **owner_headers,
            "Idempotency-Key": "original-command-key",
        },
        json=original_payload,
    )
    conflict_response = client.post(
        endpoint,
        headers={
            **owner_headers,
            "Idempotency-Key": "original-command-key",
        },
        json={
            **original_payload,
            "content": "Changed message.",
        },
    )
    new_command_response = client.post(
        endpoint,
        headers={
            **owner_headers,
            "Idempotency-Key": "new-command-key",
        },
        json=original_payload,
    )

    assert first_response.status_code == 201
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "code": "idempotency_key_conflict",
        "message": (
            "Idempotency key was already used with a different request"
        ),
    }
    assert new_command_response.status_code == 201
    assert new_command_response.json()["id"] != first_response.json()["id"]


def test_message_idempotency_key_is_scoped_to_organization(
    client: TestClient,
) -> None:
    first_organization = create_organization(
        client,
        "first-idempotency-tenant",
    )
    second_organization = create_organization(
        client,
        "second-idempotency-tenant",
    )
    first_headers = authorization_headers(
        client,
        "owner-first-idempotency-tenant@example.com",
    )
    second_headers = authorization_headers(
        client,
        "owner-second-idempotency-tenant@example.com",
    )
    first_contact = create_contact(
        client,
        first_organization["id"],
        "first-idempotency-tenant",
        first_headers,
    )
    second_contact = create_contact(
        client,
        second_organization["id"],
        "second-idempotency-tenant",
        second_headers,
    )
    first_conversation = create_conversation(
        client,
        first_organization["id"],
        first_contact["id"],
        "First tenant conversation",
        first_headers,
    )
    second_conversation = create_conversation(
        client,
        second_organization["id"],
        second_contact["id"],
        "Second tenant conversation",
        second_headers,
    )
    shared_key = "same-key-in-two-organizations"
    payload = {
        "sender_type": "AGENT",
        "content": "This key is tenant-scoped.",
    }

    first_response = client.post(
        f"/conversations/{first_conversation['id']}/messages",
        headers={
            **first_headers,
            "Idempotency-Key": shared_key,
        },
        json=payload,
    )
    second_response = client.post(
        f"/conversations/{second_conversation['id']}/messages",
        headers={
            **second_headers,
            "Idempotency-Key": shared_key,
        },
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] != second_response.json()["id"]


def test_concurrent_message_idempotency_creates_exactly_one_message(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    organization = create_organization(client, "concurrent-message-key")
    owner_email = "owner-concurrent-message-key@example.com"
    owner_headers = authorization_headers(client, owner_email)
    contact = create_contact(
        client,
        organization["id"],
        "concurrent-message-key",
        owner_headers,
    )
    conversation = create_conversation(
        client,
        organization["id"],
        contact["id"],
        "Two simultaneous retries",
        owner_headers,
    )
    owner_response = client.get("/auth/me", headers=owner_headers)
    assert owner_response.status_code == 200
    owner_id = UUID(owner_response.json()["id"])
    conversation_id = UUID(conversation["id"])
    organization_id = UUID(organization["id"])

    async def run_concurrent_requests() -> tuple[list[UUID], int, int]:
        barrier = asyncio.Barrier(2)
        original_get_by_key = idempotency_repository.get_by_key

        async def synchronized_initial_lookup(
            session: AsyncSession,
            *,
            organization_id: UUID,
            key: str,
        ) -> IdempotencyRecord | None:
            record = await original_get_by_key(
                session,
                organization_id=organization_id,
                key=key,
            )

            if record is None:
                await barrier.wait()

            return record

        monkeypatch.setattr(
            idempotency_repository,
            "get_by_key",
            synchronized_initial_lookup,
        )

        async def create_once() -> UUID:
            async with concurrent_session_factory() as session:
                stored_conversation = await session.get(
                    Conversation,
                    conversation_id,
                )
                current_user = await session.get(User, owner_id)
                assert stored_conversation is not None
                assert current_user is not None

                message = await message_service.create_message(
                    session=session,
                    conversation=stored_conversation,
                    data=MessageCreate(
                        sender_type=MessageSenderType.AGENT,
                        content="Only one concurrent message.",
                    ),
                    current_user=current_user,
                    idempotency_key="concurrent-command-key",
                )

                return message.id

        message_ids = await asyncio.wait_for(
            asyncio.gather(create_once(), create_once()),
            timeout=10,
        )

        async with concurrent_session_factory() as session:
            message_count = await session.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conversation_id,
                ),
            )
            record_count = await session.scalar(
                select(func.count(IdempotencyRecord.id)).where(
                    IdempotencyRecord.organization_id == organization_id,
                    IdempotencyRecord.key == "concurrent-command-key",
                ),
            )

        return message_ids, message_count or 0, record_count or 0

    message_ids, message_count, record_count = asyncio.run(
        run_concurrent_requests(),
    )

    assert message_ids[0] == message_ids[1]
    assert message_count == 1
    assert record_count == 1


def test_message_creation_rollback_leaves_no_partial_idempotency_data(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    organization = create_organization(client, "message-rollback")
    owner_headers = authorization_headers(
        client,
        "owner-message-rollback@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "message-rollback",
        owner_headers,
    )
    conversation = create_conversation(
        client,
        organization["id"],
        contact["id"],
        "Rollback message and idempotency record together",
        owner_headers,
    )
    owner_response = client.get("/auth/me", headers=owner_headers)
    assert owner_response.status_code == 200
    owner_id = UUID(owner_response.json()["id"])
    conversation_id = UUID(conversation["id"])
    organization_id = UUID(organization["id"])

    async def force_rollback_after_flush() -> tuple[int, int]:
        async with concurrent_session_factory() as session:
            stored_conversation = await session.get(
                Conversation,
                conversation_id,
            )
            current_user = await session.get(User, owner_id)
            assert stored_conversation is not None
            assert current_user is not None

            async def failing_commit() -> None:
                await session.flush()
                await session.rollback()
                raise RuntimeError("Force transaction rollback")

            monkeypatch.setattr(session, "commit", failing_commit)

            with pytest.raises(
                RuntimeError,
                match="Force transaction rollback",
            ):
                await message_service.create_message(
                    session=session,
                    conversation=stored_conversation,
                    data=MessageCreate(
                        sender_type=MessageSenderType.AGENT,
                        content="This message must be rolled back.",
                    ),
                    current_user=current_user,
                    idempotency_key="rollback-command-key",
                )

        async with concurrent_session_factory() as session:
            message_count = await session.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conversation_id,
                ),
            )
            record_count = await session.scalar(
                select(func.count(IdempotencyRecord.id)).where(
                    IdempotencyRecord.organization_id == organization_id,
                    IdempotencyRecord.key == "rollback-command-key",
                ),
            )

        return message_count or 0, record_count or 0

    message_count, record_count = asyncio.run(force_rollback_after_flush())

    assert message_count == 0
    assert record_count == 0


def test_conversation_validation_not_found_and_cascade(
    client: TestClient,
) -> None:
    organization = create_organization(client, "cascade-conversation")
    owner_headers = authorization_headers(
        client,
        "owner-cascade-conversation@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "cascade",
        owner_headers,
    )

    invalid_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "   ",
        },
    )
    assert invalid_response.status_code == 422

    missing_response = client.get(
        f"/conversations/{uuid4()}",
        headers=owner_headers,
    )
    assert missing_response.status_code == 404

    conversation_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Removed with organization",
        },
    )
    conversation_id = conversation_response.json()["id"]

    delete_response = client.delete(
        f"/organizations/{organization['id']}",
        headers=owner_headers,
    )
    assert delete_response.status_code == 204

    removed_response = client.get(
        f"/conversations/{conversation_id}",
        headers=owner_headers,
    )
    assert removed_response.status_code == 404
