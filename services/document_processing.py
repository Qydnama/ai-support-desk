import asyncio
import logging
from uuid import UUID

from core.exceptions import DocumentStorageUnavailableError
from database import engine, session_factory
from repositories import document_chunks as document_chunk_repository
from repositories import documents as document_repository
from services.document_chunks import build_document_chunks
from services.document_embeddings import embed_document_texts
from services.document_storage import get_document_storage
from services.document_text_extraction import (
    DocumentTextExtractionError,
    extract_document_text,
)
from services.document_vector_store import (
    upsert_document_chunk_vectors,
)

logger = logging.getLogger(__name__)


async def fail_processing_document(
    document_id: UUID,
) -> None:
    try:
        async with session_factory() as session:
            try:
                await document_repository.mark_failed(
                    session=session,
                    document_id=document_id,
                    error_message=(
                        "Document processing failed after retries."
                    ),
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()


async def process_document(
    document_id: UUID,
    *,
    task_id: str | None = None,
) -> None:
    try:
        async with session_factory() as session:
            document = (
                await document_repository.claim_pending_for_processing(
                    session=session,
                    document_id=document_id,
                )
            )

            if document is None:
                return

            await session.commit()

            logger.info(
                "document_processing_started "
                "task_id=%s document_id=%s organization_id=%s",
                task_id,
                document.id,
                document.organization_id,
            )

            try:
                content = await asyncio.to_thread(
                    get_document_storage().read_bytes,
                    document.storage_key,
                )
            except (
                FileNotFoundError,
                PermissionError,
                ValueError,
            ):
                try:
                    await document_repository.mark_failed(
                        session=session,
                        document_id=document.id,
                        error_message=(
                            "Document file cannot be read."
                        ),
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

                return
            except (
                DocumentStorageUnavailableError,
                OSError,
            ) as exc:
                logger.warning(
                    "document_processing_transient_error "
                    "task_id=%s document_id=%s "
                    "organization_id=%s error_type=%s",
                    task_id,
                    document.id,
                    document.organization_id,
                    exc.__class__.__name__,
                )
                raise

            try:
                extracted_document = await asyncio.to_thread(
                    extract_document_text,
                    content=content,
                    content_type=document.content_type,
                )

            except DocumentTextExtractionError as exc:
                try:
                    await document_repository.mark_failed(
                        session=session,
                        document_id=document.id,
                        error_message=str(exc),
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

                return
                
            chunks = build_document_chunks(
                organization_id=document.organization_id,
                document_id=document.id,
                extracted_document=extracted_document,
            )

            try:
                await document_chunk_repository.replace_for_document(
                    session=session,
                    organization_id=document.organization_id,
                    document_id=document.id,
                    chunks=chunks,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            try:
                vectors = await asyncio.to_thread(
                    embed_document_texts,
                    [chunk.content for chunk in chunks],
                )
                await asyncio.to_thread(
                    upsert_document_chunk_vectors,
                    chunks=chunks,
                    vectors=vectors,
                )
            except OSError as exc:
                logger.warning(
                    "document_vector_indexing_transient_error "
                    "task_id=%s document_id=%s "
                    "organization_id=%s error_type=%s",
                    task_id,
                    document.id,
                    document.organization_id,
                    exc.__class__.__name__,
                )
                raise

            try:
                await document_repository.mark_completed(
                    session=session,
                    document_id=document.id,
                    extracted_text=extracted_document.text,
                )
                await session.commit()
                logger.info(
                    "document_processing_completed "
                    "task_id=%s document_id=%s "
                    "organization_id=%s",
                    task_id,
                    document.id,
                    document.organization_id,
                )
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
