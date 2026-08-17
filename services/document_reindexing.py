import argparse
import asyncio
import logging
from uuid import UUID

from core.enums import DocumentStatus
from database import engine, session_factory
from repositories import document_chunks as document_chunk_repository
from repositories import documents as document_repository
from services.document_chunks import build_document_chunks
from services.document_embeddings import embed_document_texts
from services.document_storage import get_document_storage
from services.document_text_extraction import extract_document_text
from services.document_vector_store import (
    upsert_document_chunk_vectors,
)
from settings import settings

logger = logging.getLogger(__name__)


async def reindex_completed_documents(
    *,
    batch_size: int,
) -> int:
    reindexed_count = 0

    while True:
        async with session_factory() as session:
            documents = (
                await document_chunk_repository
                .list_completed_without_index_version(
                    session=session,
                    index_version=(
                        settings.document_chunk_index_version
                    ),
                    limit=batch_size,
                )
            )

        if not documents:
            return reindexed_count

        for document in documents:
            was_reindexed = await reindex_document(
                document.id,
            )

            if was_reindexed:
                reindexed_count += 1


async def reindex_document(
    document_id: UUID,
) -> bool:
    async with session_factory() as session:
        document = await document_repository.get_by_id(
            session=session,
            document_id=document_id,
        )

        if (
            document is None
            or document.status != DocumentStatus.COMPLETED
        ):
            return False

        try:
            content = await asyncio.to_thread(
                get_document_storage().read_bytes,
                document.storage_key,
            )
        except FileNotFoundError:
            try:
                await document_repository.mark_completed_as_failed(
                    session=session,
                    document_id=document.id,
                    error_message=(
                        "Document file is unavailable for reindexing."
                    ),
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            logger.warning(
                "document_reindexing_source_missing "
                "document_id=%s organization_id=%s",
                document.id,
                document.organization_id,
            )

            return False
        extracted_document = await asyncio.to_thread(
            extract_document_text,
            content=content,
            content_type=document.content_type,
        )
        chunks = build_document_chunks(
            organization_id=document.organization_id,
            document_id=document.id,
            extracted_document=extracted_document,
        )
        vectors = await asyncio.to_thread(
            embed_document_texts,
            [chunk.content for chunk in chunks],
        )

        # Сначала Qdrant, затем PostgreSQL.
        # Если Qdrant недоступен, старые PG-чанки остаются нетронутыми.
        await asyncio.to_thread(
            upsert_document_chunk_vectors,
            chunks=chunks,
            vectors=vectors,
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

        logger.info(
            "document_reindexed "
            "document_id=%s organization_id=%s index_version=%s",
            document.id,
            document.organization_id,
            settings.document_chunk_index_version,
        )

        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reindex completed documents into the current "
            "document index version."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")

    return args


async def run_command(
    *,
    batch_size: int,
) -> None:
    try:
        reindexed_count = await reindex_completed_documents(
            batch_size=batch_size,
        )
    finally:
        await engine.dispose()

    logger.info(
        "document_reindexing_finished reindexed_count=%s",
        reindexed_count,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arguments = parse_args()

    asyncio.run(
        run_command(
            batch_size=arguments.batch_size,
        ),
    )