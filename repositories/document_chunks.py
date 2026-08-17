from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.enums import DocumentStatus
from models.document_chunks import DocumentChunk
from models.documents import Document


async def replace_for_document(
    session: AsyncSession,
    *,
    organization_id: UUID,
    document_id: UUID,
    chunks: Sequence[DocumentChunk],
) -> None:
    await session.execute(
        delete(DocumentChunk).where(
            DocumentChunk.organization_id == organization_id,
            DocumentChunk.document_id == document_id,
        ),
    )
    session.add_all(chunks)


async def list_completed_by_ids(
    session: AsyncSession,
    *,
    organization_id: UUID,
    index_version: str,
    chunk_ids: Sequence[UUID],
) -> list[DocumentChunk]:
    if not chunk_ids:
        return []

    chunks = await session.scalars(
        select(DocumentChunk)
        .join(DocumentChunk.document)
        .options(joinedload(DocumentChunk.document))
        .where(
            DocumentChunk.organization_id == organization_id,
            DocumentChunk.id.in_(chunk_ids),
            DocumentChunk.index_version == index_version,
            Document.organization_id == organization_id,
            Document.status == DocumentStatus.COMPLETED,
        ),
    )

    return list(chunks)


async def list_completed_without_index_version(
    session: AsyncSession,
    *,
    index_version: str,
    limit: int,
) -> list[Document]:
    has_required_index_version = (
        select(DocumentChunk.id)
        .where(
            DocumentChunk.document_id == Document.id,
            DocumentChunk.index_version == index_version,
        )
        .exists()
    )

    documents = await session.scalars(
        select(Document)
        .where(
            Document.status == DocumentStatus.COMPLETED,
            ~has_required_index_version,
        )
        .order_by(
            Document.created_at,
            Document.id,
        )
        .limit(limit),
    )

    return list(documents)