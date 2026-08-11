import logging
from datetime import UTC, datetime, timedelta

from database import engine, session_factory
from repositories import documents as document_repository
from settings import settings

logger = logging.getLogger(__name__)


async def fail_stale_processing_documents(
    *,
    task_id: str | None = None,
) -> int:
    stale_before = (
        datetime.now(UTC)
        - timedelta(
            seconds=(
                settings.document_processing_stale_after_seconds
            ),
        )
    )

    try:
        async with session_factory() as session:
            try:
                failed_count = (
                    await document_repository
                    .mark_stale_processing_as_failed(
                        session=session,
                        stale_before=stale_before,
                    )
                )
                await session.commit()
                
                logger.info(
                    "document_stale_processing_recovery_completed "
                    "task_id=%s failed_count=%s",
                    task_id,
                    failed_count,
                )
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()

    return failed_count