import asyncio
from hashlib import sha256
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import DocumentStatus
from core.exceptions import DocumentSearchUnavailableError
from models.document_chunks import DocumentChunk
from models.documents import Document
from models.organizations import Organization
from models.users import User
from services import document_search
from services.document_answer_generation import (
    DocumentAnswerGenerationUnavailableError,
    GeneratedDocumentAnswer,
    _validate_generated_answer,
)
from services.document_vector_store import (
    DocumentVectorSearchResult,
)
from settings import settings


def create_completed_document_chunks(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID, UUID, UUID]:
    organization_id = uuid4()
    user_id = uuid4()
    document_id = uuid4()
    chunk_id = uuid4()
    foreign_organization_id = uuid4()
    foreign_user_id = uuid4()
    foreign_document_id = uuid4()
    foreign_chunk_id = uuid4()
    suffix = uuid4().hex

    async def create() -> None:
        async with session_factory() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        name="Document search user",
                        email=(
                            f"document-search-{suffix}@example.com"
                        ),
                    ),
                    Organization(
                        id=organization_id,
                        name="Document search organization",
                        slug=f"document-search-{suffix}",
                    ),
                    User(
                        id=foreign_user_id,
                        name="Foreign document search user",
                        email=(
                            f"foreign-document-search-{suffix}"
                            "@example.com"
                        ),
                    ),
                    Organization(
                        id=foreign_organization_id,
                        name="Foreign document search organization",
                        slug=f"foreign-document-search-{suffix}",
                    ),
                    Document(
                        id=document_id,
                        organization_id=organization_id,
                        uploaded_by_user_id=user_id,
                        original_filename="refunds.txt",
                        content_type="text/plain",
                        storage_key=(
                            f"documents/{document_id}.txt"
                        ),
                        status=DocumentStatus.COMPLETED,
                    ),
                    Document(
                        id=foreign_document_id,
                        organization_id=foreign_organization_id,
                        uploaded_by_user_id=foreign_user_id,
                        original_filename="foreign.txt",
                        content_type="text/plain",
                        storage_key=(
                            f"documents/{foreign_document_id}.txt"
                        ),
                        status=DocumentStatus.COMPLETED,
                    ),
                    DocumentChunk(
                        id=chunk_id,
                        organization_id=organization_id,
                        document_id=document_id,
                        chunk_index=0,
                        content=(
                            "Refunds are available within 30 days."
                        ),
                        content_hash=sha256(
                            b"Refunds are available within 30 days."
                        ).hexdigest(),
                        page_start=None,
                        page_end=None,
                        index_version=(
                            settings.document_chunk_index_version
                        ),
                    ),
                    DocumentChunk(
                        id=foreign_chunk_id,
                        organization_id=foreign_organization_id,
                        document_id=foreign_document_id,
                        chunk_index=0,
                        content="Foreign organization secret.",
                        content_hash=sha256(
                            b"Foreign organization secret."
                        ).hexdigest(),
                        page_start=None,
                        page_end=None,
                        index_version=(
                            settings.document_chunk_index_version
                        ),
                    ),
                ],
            )
            await session.commit()

    asyncio.run(create())

    return (
        organization_id,
        document_id,
        chunk_id,
        foreign_chunk_id,
    )


def test_search_uses_only_postgresql_verified_chunks(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        organization_id,
        document_id,
        chunk_id,
        foreign_chunk_id,
    ) = create_completed_document_chunks(
        concurrent_session_factory,
    )
    generated_sources: list[list[str]] = []

    monkeypatch.setattr(
        document_search,
        "embed_document_texts",
        lambda _: [[0.1, 0.2]],
    )
    monkeypatch.setattr(
        document_search,
        "search_document_chunk_vectors",
        lambda **_: [
            DocumentVectorSearchResult(
                chunk_id=foreign_chunk_id,
                score=0.99,
            ),
            DocumentVectorSearchResult(
                chunk_id=chunk_id,
                score=0.95,
            ),
        ],
    )

    def generate_answer(
        *,
        question: str,
        source_texts: list[str],
    ) -> GeneratedDocumentAnswer:
        assert question == "When can I request a refund?"
        generated_sources.append(source_texts)

        return GeneratedDocumentAnswer(
            answer="You can request a refund within 30 days.",
            answer_not_found=False,
            citation_numbers=[1],
        )

    monkeypatch.setattr(
        document_search,
        "generate_document_answer",
        generate_answer,
    )

    async def search() -> document_search.DocumentSearchResult:
        async with concurrent_session_factory() as session:
            return await document_search.search_documents(
                session=session,
                organization_id=organization_id,
                question="When can I request a refund?",
                limit=5,
            )

    result = asyncio.run(search())

    assert generated_sources == [
        ["Refunds are available within 30 days."],
    ]
    assert result.answer == "You can request a refund within 30 days."
    assert result.answer_not_found is False
    assert len(result.citations) == 1
    assert result.citations[0].document_id == document_id
    assert result.citations[0].chunk_id == chunk_id


def test_search_converts_embedding_outage_to_domain_error(
    concurrent_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable_embedding(_: list[str]) -> list[list[float]]:
        raise OSError("OpenAI is temporarily unavailable")

    monkeypatch.setattr(
        document_search,
        "embed_document_texts",
        unavailable_embedding,
    )

    async def search() -> None:
        async with concurrent_session_factory() as session:
            with pytest.raises(DocumentSearchUnavailableError):
                await document_search.search_documents(
                    session=session,
                    organization_id=uuid4(),
                    question="Any question",
                    limit=5,
                )

    asyncio.run(search())


def test_answer_validation_rejects_unknown_citation() -> None:
    generated_answer = GeneratedDocumentAnswer(
        answer="Refunds are available within 30 days.",
        answer_not_found=False,
        citation_numbers=[2],
    )

    with pytest.raises(
        DocumentAnswerGenerationUnavailableError,
        match="unknown citation number",
    ):
        _validate_generated_answer(
            generated_answer=generated_answer,
            source_count=1,
        )
