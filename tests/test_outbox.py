import asyncio
from types import SimpleNamespace

import pytest
from kombu.exceptions import OperationalError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.outbox_messages import OutboxMessage
from services import outbox


class DisposableTestEngine:
    def __init__(self) -> None:
        self.dispose_calls = 0

    async def dispose(self) -> None:
        self.dispose_calls += 1


def create_outbox_message(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    document_id: str,
) -> None:
    async def create() -> None:
        async with session_factory() as session:
            session.add(
                OutboxMessage(
                    task_name="documents.process_document",
                    payload={"args": [document_id]},
                ),
            )
            await session.commit()

    asyncio.run(create())


def read_outbox_message(
    session_factory: async_sessionmaker[AsyncSession],
) -> OutboxMessage | None:
    async def read() -> OutboxMessage | None:
        async with session_factory() as session:
            return await session.scalar(
                select(OutboxMessage),
            )

    return asyncio.run(read())


def test_outbox_publisher_marks_message_after_successful_publish(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    create_outbox_message(
        concurrent_session_factory,
        document_id="document-123",
    )
    test_engine = DisposableTestEngine()
    published_tasks: list[tuple[str, list[str]]] = []

    def publish_task(
        task_name: str,
        *,
        args: list[str],
    ) -> None:
        published_tasks.append((task_name, args))

    monkeypatch.setattr(
        outbox,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(outbox, "engine", test_engine)

    published_count = asyncio.run(
        outbox.publish_pending_messages(
            publish_task=publish_task,
            task_id="outbox-task-123",
        ),
    )
    message = read_outbox_message(concurrent_session_factory)

    assert published_count == 1
    assert published_tasks == [
        ("documents.process_document", ["document-123"]),
    ]
    assert message is not None
    assert message.published_at is not None
    assert test_engine.dispose_calls == 1

    assert asyncio.run(
        outbox.publish_pending_messages(
            publish_task=publish_task,
        ),
    ) == 0
    assert published_tasks == [
        ("documents.process_document", ["document-123"]),
    ]


def test_outbox_publisher_keeps_message_pending_after_broker_failure(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    create_outbox_message(
        concurrent_session_factory,
        document_id="document-123",
    )
    test_engine = DisposableTestEngine()

    def publish_task(*args, **kwargs) -> None:
        raise OperationalError("broker unavailable")

    monkeypatch.setattr(
        outbox,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(outbox, "engine", test_engine)

    with pytest.raises(OperationalError, match="broker unavailable"):
        asyncio.run(
            outbox.publish_pending_messages(
                publish_task=publish_task,
            ),
        )

    message = read_outbox_message(concurrent_session_factory)
    assert message is not None
    assert message.published_at is None
    assert test_engine.dispose_calls == 1
