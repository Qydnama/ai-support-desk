import asyncio
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import DocumentStatus
from models.documents import Document
from models.organizations import Organization
from models.users import User
from services import document_reindexing


def create_completed_document(
    session_factory: async_sessionmaker[AsyncSession],
) -> UUID:
    organization_id = uuid4()
    user_id = uuid4()
    document_id = uuid4()
    suffix = uuid4().hex

    async def create() -> None:
        async with session_factory() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        name="Document reindexing user",
                        email=(
                            f"document-reindexing-{suffix}"
                            "@example.com"
                        ),
                    ),
                    Organization(
                        id=organization_id,
                        name="Document reindexing organization",
                        slug=f"document-reindexing-{suffix}",
                    ),
                    Document(
                        id=document_id,
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="guide.txt",
                        content_type="text/plain",
                        storage_key=(
                            f"documents/{document_id}.txt"
                        ),
                        status=DocumentStatus.COMPLETED,
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


def test_reindexing_marks_missing_source_as_failed(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    document_id = create_completed_document(
        concurrent_session_factory,
    )

    def read_bytes(_: str) -> bytes:
        raise FileNotFoundError("document object does not exist")

    monkeypatch.setattr(
        document_reindexing,
        "session_factory",
        concurrent_session_factory,
    )
    monkeypatch.setattr(
        document_reindexing,
        "get_document_storage",
        lambda: SimpleNamespace(read_bytes=read_bytes),
    )

    was_reindexed = asyncio.run(
        document_reindexing.reindex_document(document_id),
    )

    document = read_document(
        concurrent_session_factory,
        document_id,
    )

    assert was_reindexed is False
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == (
        "Document file is unavailable for reindexing."
    )
