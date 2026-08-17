from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import DocumentStatus
from models.documents import Document


async def get_by_id(
    session: AsyncSession,
    *,
    document_id: UUID,
    organization_id: UUID | None = None,
) -> Document | None:
    statement = select(Document).where(
        Document.id == document_id,
    )

    if organization_id is not None:
        statement = statement.where(
            Document.organization_id == organization_id,
        )

    return await session.scalar(statement)


async def list_by_organization(
    session: AsyncSession,
    *,
    organization_id: UUID,
    limit: int,
    offset: int,
) -> list[Document]:
    statement = (
        select(Document)
        .where(
            Document.organization_id == organization_id,
        )
        .order_by(
            Document.created_at,
            Document.id,
        )
        .offset(offset)
        .limit(limit)
    )

    documents = await session.scalars(statement)

    return list(documents)


async def claim_pending_for_processing(
    session: AsyncSession,
    *,
    document_id: UUID,
) -> Document | None:
    statement = (
        update(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PENDING,
        )
        .values(
            status=DocumentStatus.PROCESSING,
            processing_started_at=func.now(),
            error_message=None,
        )
        .returning(Document)
    )

    return await session.scalar(statement)


async def mark_completed(
    session: AsyncSession,
    *,
    document_id: UUID,
    extracted_text: str,
) -> Document | None:
    statement = (
        update(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PROCESSING,
        )
        .values(
            status=DocumentStatus.COMPLETED,
            extracted_text=extracted_text,
            error_message=None,
        )
        .returning(Document)
    )

    return await session.scalar(statement)


async def mark_failed(
    session: AsyncSession,
    *,
    document_id: UUID,
    error_message: str,
) -> Document | None:
    statement = (
        update(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PROCESSING,
        )
        .values(
            status=DocumentStatus.FAILED,
            error_message=error_message,
        )
        .returning(Document)
    )

    return await session.scalar(statement)


async def mark_stale_processing_as_failed(
    session: AsyncSession,
    *,
    stale_before: datetime,
) -> int:
    statement = (
        update(Document)
        .where(
            Document.status == DocumentStatus.PROCESSING,
            Document.processing_started_at < stale_before,
        )
        .values(
            status=DocumentStatus.FAILED,
            error_message=(
                "Document processing timed out."
            ),
        )
        .returning(Document.id)
    )

    failed_document_ids = await session.scalars(
        statement,
    )

    return len(list(failed_document_ids))


async def mark_completed_as_failed(
    session: AsyncSession,
    *,
    document_id: UUID,
    error_message: str,
) -> Document | None:
    statement = (
        update(Document)
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.COMPLETED,
        )
        .values(
            status=DocumentStatus.FAILED,
            error_message=error_message,
        )
        .returning(Document)
    )

    return await session.scalar(statement)