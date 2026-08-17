import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import DocumentStatus
from models.documents import Document
from models.organizations import Organization
from models.users import User
from services import document_maintenance
from services import document_processing
from services.document_storage import DocumentStorage
from settings import settings


class DisposableTestEngine:
    def __init__(self) -> None:
        self.dispose_calls = 0

    async def dispose(self) -> None:
        self.dispose_calls += 1


def create_pending_document(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    storage_key: str,
    status: DocumentStatus = DocumentStatus.PENDING,
    processing_started_at: datetime | None = None,
) -> UUID:
    document_id = uuid4()
    organization_id = uuid4()
    user_id = uuid4()
    suffix = uuid4().hex

    async def create() -> None:
        async with session_factory() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        name="Document processor",
                        email=f"processor-{suffix}@example.com",
                    ),
                    Organization(
                        id=organization_id,
                        name=f"Document processing organization {suffix}",
                        slug=f"document-processing-{suffix}",
                    ),
                    Document(
                        id=document_id,
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="guide.txt",
                        content_type="text/plain",
                        storage_key=storage_key,
                        status=status,
                        processing_started_at=processing_started_at,
                    ),
                ],
            )
            await session.commit()

    asyncio.run(create())

    return document_id


def read_document(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: UUID,
) -> Document | None:
    async def read() -> Document | None:
        async with session_factory() as session:
            return await session.get(Document, document_id)

    return asyncio.run(read())


def test_document_processor_completes_once(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    storage = DocumentStorage(tmp_path)
    storage_key = "documents/guide.txt"
    storage.write_bytes(storage_key, b"Knowledge base guide")
    document_id = create_pending_document(
        concurrent_session_factory,
        storage_key=storage_key,
    )
    test_engine = DisposableTestEngine()
    read_calls: list[str] = []

    def read_bytes(key: str) -> bytes:
        read_calls.append(key)
        return storage.read_bytes(key)

    monkeypatch.setattr(
        document_processing,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(
        document_processing,
        "engine",
        test_engine,
    )
    monkeypatch.setattr(
        document_processing,
        "get_document_storage",
        lambda: SimpleNamespace(read_bytes=read_bytes),
    )
    monkeypatch.setattr(
        document_processing,
        "embed_document_texts",
        lambda texts: [[0.1] for _ in texts],
    )
    monkeypatch.setattr(
        document_processing,
        "upsert_document_chunk_vectors",
        lambda **_: None,
    )
    caplog.set_level(
        "INFO",
        logger=document_processing.__name__,
    )

    asyncio.run(
        document_processing.process_document(
            document_id,
            task_id="document-task-123",
        ),
    )
    asyncio.run(document_processing.process_document(document_id))

    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    assert document.status == DocumentStatus.COMPLETED
    assert document.extracted_text == "Knowledge base guide"
    assert document.error_message is None
    assert document.processing_started_at is not None
    assert read_calls == [storage_key]
    assert test_engine.dispose_calls == 2
    log_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == document_processing.__name__
    ]
    assert any(
        "document_processing_started "
        "task_id=document-task-123 "
        f"document_id={document_id} "
        f"organization_id={document.organization_id}"
        in message
        for message in log_messages
    )
    assert any(
        "document_processing_completed "
        "task_id=document-task-123 "
        f"document_id={document_id} "
        f"organization_id={document.organization_id}"
        in message
        for message in log_messages
    )
    assert "Knowledge base guide" not in "\n".join(log_messages)


def test_document_processor_marks_missing_file_as_failed(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
    tmp_path,
) -> None:
    document_id = create_pending_document(
        concurrent_session_factory,
        storage_key="documents/missing.txt",
    )
    test_engine = DisposableTestEngine()

    monkeypatch.setattr(
        document_processing,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(
        document_processing,
        "engine",
        test_engine,
    )
    monkeypatch.setattr(
        document_processing,
        "get_document_storage",
        lambda: DocumentStorage(tmp_path),
    )

    asyncio.run(document_processing.process_document(document_id))

    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert document.extracted_text is None
    assert document.error_message
    assert document.processing_started_at is not None
    assert test_engine.dispose_calls == 1


def test_document_processor_leaves_transient_storage_error_for_retry(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
    caplog,
) -> None:
    document_id = create_pending_document(
        concurrent_session_factory,
        storage_key="documents/temporarily-unavailable.txt",
    )
    test_engine = DisposableTestEngine()

    def read_bytes(_: str) -> bytes:
        raise OSError("temporary storage failure")

    monkeypatch.setattr(
        document_processing,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(
        document_processing,
        "engine",
        test_engine,
    )
    monkeypatch.setattr(
        document_processing,
        "get_document_storage",
        lambda: SimpleNamespace(read_bytes=read_bytes),
    )
    caplog.set_level(
        "WARNING",
        logger=document_processing.__name__,
    )

    with pytest.raises(OSError, match="temporary storage failure"):
        asyncio.run(
            document_processing.process_document(
                document_id,
                task_id="document-task-retry",
            ),
        )

    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    assert document.status == DocumentStatus.PROCESSING

    asyncio.run(
        document_processing.fail_processing_document(document_id),
    )

    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == (
        "Document processing failed after retries."
    )
    assert test_engine.dispose_calls == 2
    log_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == document_processing.__name__
    ]
    assert any(
        "document_processing_transient_error "
        "task_id=document-task-retry "
        f"document_id={document_id} "
        f"organization_id={document.organization_id} "
        "error_type=OSError"
        in message
        for message in log_messages
    )
    assert "temporary storage failure" not in "\n".join(log_messages)


def test_document_maintenance_marks_only_stale_processing_documents(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
    caplog,
) -> None:
    stale_document_id = create_pending_document(
        concurrent_session_factory,
        storage_key="documents/stale.txt",
        status=DocumentStatus.PROCESSING,
        processing_started_at=(
            datetime.now(UTC) - timedelta(minutes=11)
        ),
    )
    active_document_id = create_pending_document(
        concurrent_session_factory,
        storage_key="documents/active.txt",
        status=DocumentStatus.PROCESSING,
        processing_started_at=datetime.now(UTC),
    )
    test_engine = DisposableTestEngine()

    monkeypatch.setattr(
        document_maintenance,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(
        document_maintenance,
        "engine",
        test_engine,
    )
    monkeypatch.setattr(
        settings,
        "document_processing_stale_after_seconds",
        600,
    )
    caplog.set_level(
        "INFO",
        logger=document_maintenance.__name__,
    )

    failed_count = asyncio.run(
        document_maintenance.fail_stale_processing_documents(
            task_id="maintenance-task-123",
        ),
    )

    stale_document = read_document(
        concurrent_session_factory,
        stale_document_id,
    )
    active_document = read_document(
        concurrent_session_factory,
        active_document_id,
    )
    assert failed_count == 1
    assert stale_document is not None
    assert stale_document.status == DocumentStatus.FAILED
    assert stale_document.error_message == (
        "Document processing timed out."
    )
    assert active_document is not None
    assert active_document.status == DocumentStatus.PROCESSING
    assert test_engine.dispose_calls == 1
    log_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == document_maintenance.__name__
    ]
    assert log_messages == [
        "document_stale_processing_recovery_completed "
        "task_id=maintenance-task-123 failed_count=1",
    ]
