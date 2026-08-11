from uuid import uuid4

from celery import states

from celery_app import celery_app
from settings import settings
from services import document_processing
from services import outbox
from tasks import documents as document_tasks


def test_document_task_retries_transient_error_and_marks_failed(
    monkeypatch,
) -> None:
    document_id = uuid4()
    attempts = 0
    failed_document_ids = []

    async def raise_transient_error(
        _,
        *,
        task_id: str | None = None,
    ) -> None:
        nonlocal attempts
        attempts += 1
        raise OSError("temporary storage failure")

    async def mark_failed_after_retries(failed_document_id) -> None:
        failed_document_ids.append(failed_document_id)

    monkeypatch.setattr(
        document_processing,
        "process_document",
        raise_transient_error,
    )
    monkeypatch.setattr(
        document_processing,
        "fail_processing_document",
        mark_failed_after_retries,
    )

    result = document_tasks.process_document.apply(
        args=[str(document_id)],
    )

    assert result.state == states.FAILURE
    assert attempts == 4
    assert failed_document_ids == [document_id]


def test_document_task_marks_permanent_error_without_retry(
    monkeypatch,
) -> None:
    document_id = uuid4()
    attempts = 0
    failed_document_ids = []

    async def raise_permanent_error(
        _,
        *,
        task_id: str | None = None,
    ) -> None:
        nonlocal attempts
        attempts += 1
        raise FileNotFoundError("document file is missing")

    async def mark_failed(failed_document_id) -> None:
        failed_document_ids.append(failed_document_id)

    monkeypatch.setattr(
        document_processing,
        "process_document",
        raise_permanent_error,
    )
    monkeypatch.setattr(
        document_processing,
        "fail_processing_document",
        mark_failed,
    )

    result = document_tasks.process_document.apply(
        args=[str(document_id)],
    )

    assert result.state == states.FAILURE
    assert attempts == 1
    assert failed_document_ids == [document_id]


def test_stale_document_task_runs_maintenance_service(
    monkeypatch,
) -> None:
    calls = 0
    task_ids: list[str | None] = []

    async def fail_stale_processing_documents(
        *,
        task_id: str | None = None,
    ) -> int:
        nonlocal calls
        calls += 1
        task_ids.append(task_id)
        return 0

    monkeypatch.setattr(
        document_tasks.document_maintenance,
        "fail_stale_processing_documents",
        fail_stale_processing_documents,
    )

    result = document_tasks.fail_stale_processing_documents.apply()

    assert calls == 1
    assert task_ids == [result.id]


def test_beat_schedules_stale_document_maintenance() -> None:
    schedule = celery_app.conf.beat_schedule[
        "fail-stale-document-processing"
    ]

    assert schedule["task"] == "documents.fail_stale_processing"
    assert schedule["schedule"] == (
        settings.document_maintenance_interval_seconds
    )


def test_outbox_publisher_task_runs_service(
    monkeypatch,
) -> None:
    task_ids: list[str | None] = []

    async def publish_pending_messages(
        *,
        publish_task,
        task_id: str | None = None,
    ) -> int:
        assert publish_task.__self__ is celery_app
        task_ids.append(task_id)
        return 0

    monkeypatch.setattr(
        outbox,
        "publish_pending_messages",
        publish_pending_messages,
    )

    result = document_tasks.publish_pending_outbox_messages.apply()

    assert task_ids == [result.id]


def test_beat_schedules_outbox_publisher() -> None:
    schedule = celery_app.conf.beat_schedule[
        "publish-pending-outbox-messages"
    ]

    assert schedule["task"] == "outbox.publish_pending"
    assert schedule["schedule"] == settings.outbox_publish_interval_seconds
