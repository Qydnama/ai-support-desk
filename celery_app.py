from celery import Celery

from settings import settings

celery_app = Celery(
    "crud",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.documents"],
)

celery_app.conf.update(
    task_default_queue="crud.default.v1",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    result_expires=3_600,
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_enable_remote_control=False,
    beat_schedule={
        "fail-stale-document-processing": {
            "task": "documents.fail_stale_processing",
            "schedule": (
                settings.document_maintenance_interval_seconds
            ),
        },
        "publish-pending-outbox-messages": {
            "task": "outbox.publish_pending",
            "schedule": settings.outbox_publish_interval_seconds,
        },
    },
)
