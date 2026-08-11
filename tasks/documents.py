import asyncio
import logging
from uuid import UUID

from celery import Task
from kombu.exceptions import OperationalError

from celery_app import celery_app
from services import document_maintenance, document_processing, outbox

logger = logging.getLogger(__name__)


class DocumentProcessingTask(Task):
    autoretry_for = (OSError,)
    dont_autoretry_for = (
        FileNotFoundError,
        PermissionError,
    )
    retry_backoff = 2
    retry_backoff_max = 60
    retry_jitter = True
    max_retries = 3

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        einfo: object,
    ) -> None:
        super().on_failure(
            exc,
            task_id,
            args,
            kwargs,
            einfo,
        )

        if not isinstance(exc, OSError):
            return

        try:
            document_id = UUID(str(args[0]))
        except (
            IndexError,
            TypeError,
            ValueError,
        ):
            return

        logger.error(
            "document_processing_retries_exhausted "
            "task_id=%s document_id=%s error_type=%s",
            task_id,
            document_id,
            exc.__class__.__name__,
        )

        asyncio.run(
            document_processing.fail_processing_document(
                document_id,
            ),
        )


class OutboxPublisherTask(Task):
    autoretry_for = (OperationalError,)
    retry_backoff = 2
    retry_backoff_max = 60
    retry_jitter = True
    max_retries = 3

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        einfo: object,
    ) -> None:
        super().on_failure(
            exc,
            task_id,
            args,
            kwargs,
            einfo,
        )
        logger.error(
            "outbox_publisher_failed "
            "task_id=%s error_type=%s",
            task_id,
            exc.__class__.__name__,
        )


@celery_app.task(
    base=DocumentProcessingTask,
    bind=True,
    name="documents.process_document",
    ignore_result=True,
)
def process_document(
    self: DocumentProcessingTask,
    document_id: str,
) -> None:
    asyncio.run(
        document_processing.process_document(
            UUID(document_id),
            task_id=self.request.id,
        ),
    )


@celery_app.task(
    bind=True,
    name="documents.fail_stale_processing",
    ignore_result=True,
)
def fail_stale_processing_documents(
    self: Task,
) -> None:
    asyncio.run(
        document_maintenance.fail_stale_processing_documents(
            task_id=self.request.id,
        ),
    )


@celery_app.task(
    base=OutboxPublisherTask,
    bind=True,
    name="outbox.publish_pending",
    ignore_result=True,
)
def publish_pending_outbox_messages(
    self: OutboxPublisherTask,
) -> None:
    asyncio.run(
        outbox.publish_pending_messages(
            publish_task=celery_app.send_task,
            task_id=self.request.id,
        ),
    )
