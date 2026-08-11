import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from database import engine, session_factory
from repositories import outbox_messages as outbox_message_repository
from settings import settings

logger = logging.getLogger(__name__)

TaskPublisher = Callable[..., Any]


async def publish_pending_messages(
    *,
    publish_task: TaskPublisher,
    task_id: str | None = None,
) -> int:
    try:
        async with session_factory() as session:
            try:
                messages = (
                    await outbox_message_repository
                    .list_pending_for_publish(
                        session=session,
                        limit=settings.outbox_publish_batch_size,
                    )
                )

                for message in messages:
                    args = message.payload["args"]

                    await asyncio.to_thread(
                        publish_task,
                        message.task_name,
                        args=args,
                    )
                    message.published_at = datetime.now(UTC)

                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()

    logger.info(
        "outbox_messages_published "
        "task_id=%s published_count=%s",
        task_id,
        len(messages),
    )

    return len(messages)
