import asyncio
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import DocumentSearchUnavailableError
from models.document_chunks import DocumentChunk
from repositories import document_chunks as document_chunk_repository
from services.document_answer_generation import (
    generate_document_answer,
)
from services.document_embeddings import embed_document_texts
from services.document_vector_store import (
    DocumentVectorSearchResult,
    search_document_chunk_vectors,
)
from settings import settings


@dataclass(frozen=True, slots=True)
class DocumentSearchCitation:
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    document_filename: str
    page_start: int | None
    page_end: int | None
    score: float


@dataclass(frozen=True, slots=True)
class DocumentSearchResult:
    answer: str | None
    answer_not_found: bool
    citations: tuple[DocumentSearchCitation, ...]


async def search_documents(
    session: AsyncSession,
    *,
    organization_id: UUID,
    question: str,
    limit: int,
) -> DocumentSearchResult:
    try:
        vectors = await asyncio.to_thread(
            embed_document_texts,
            [question],
        )
        candidates = await asyncio.to_thread(
            search_document_chunk_vectors,
            organization_id=organization_id,
            vector=vectors[0],
            limit=limit,
            score_threshold=(
                settings.document_search_score_threshold
            ),
        )
    except OSError as exc:
        raise DocumentSearchUnavailableError() from exc

    chunks = await document_chunk_repository.list_completed_by_ids(
        session=session,
        organization_id=organization_id,
        chunk_ids=[
            candidate.chunk_id
            for candidate in candidates
        ],
        index_version=settings.document_chunk_index_version,
    )
    ordered_chunks = _order_chunks_by_candidates(
        chunks=chunks,
        candidates=candidates,
    )

    if not ordered_chunks:
        return DocumentSearchResult(
            answer=None,
            answer_not_found=True,
            citations=(),
        )

    available_citations = tuple(
        DocumentSearchCitation(
            document_id=chunk.document_id,
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            document_filename=chunk.document.original_filename,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            score=score,
        )
        for chunk, score in ordered_chunks
    )

    try:
        generated_answer = await asyncio.to_thread(
            generate_document_answer,
            question=question,
            source_texts=[
                chunk.content
                for chunk, _ in ordered_chunks
            ],
        )
    except OSError as exc:
        raise DocumentSearchUnavailableError() from exc

    if generated_answer.answer_not_found:
        return DocumentSearchResult(
            answer=None,
            answer_not_found=True,
            citations=(),
        )

    selected_citation_numbers = tuple(
        dict.fromkeys(
            generated_answer.citation_numbers,
        )
    )

    return DocumentSearchResult(
        answer=generated_answer.answer,
        answer_not_found=False,
        citations=tuple(
            available_citations[citation_number - 1]
            for citation_number in selected_citation_numbers
        ),
    )


def _order_chunks_by_candidates(
    *,
    chunks: list[DocumentChunk],
    candidates: list[DocumentVectorSearchResult],
) -> list[tuple[DocumentChunk, float]]:
    chunks_by_id = {
        chunk.id: chunk
        for chunk in chunks
    }

    return [
        (
            chunks_by_id[candidate.chunk_id],
            candidate.score,
        )
        for candidate in candidates
        if candidate.chunk_id in chunks_by_id
    ]