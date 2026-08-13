import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from celery_app import celery_app
from services import documents as document_service
from services.document_storage import DocumentStorage
from settings import settings
from models.outbox_messages import OutboxMessage


def create_organization(
    client: TestClient,
    suffix: str,
) -> tuple[dict[str, str], dict[str, str]]:
    email = f"document-upload-{suffix}@example.com"
    password = "correct-horse-battery-staple"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Document uploader {suffix}",
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={
            "name": f"Document upload organization {suffix}",
            "slug": f"document-upload-{suffix}",
        },
    )
    assert organization_response.status_code == 201

    return organization_response.json(), headers


def configure_document_upload(
    monkeypatch,
    tmp_path: Path,
) -> list[tuple[str, list[str] | None]]:
    queued_tasks: list[tuple[str, list[str] | None]] = []

    def send_task(
        task_name: str,
        *,
        args: list[str] | None = None,
    ) -> None:
        queued_tasks.append((task_name, args))

    monkeypatch.setattr(
        document_service,
        "get_document_storage",
        lambda: DocumentStorage(tmp_path),
    )
    monkeypatch.setattr(
        celery_app,
        "send_task",
        send_task,
    )

    return queued_tasks


def test_upload_document_saves_file_and_queues_processing(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, headers = create_organization(client, "success")
    queued_tasks = configure_document_upload(monkeypatch, tmp_path)
    path = f"/organizations/{organization['id']}/documents"

    response = client.post(
        path,
        headers=headers,
        files={
            "file": (
                "guide.txt",
                b"Knowledge base guide",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 201
    document = response.json()
    assert document["organization_id"] == organization["id"]
    assert document["original_filename"] == "guide.txt"
    assert document["content_type"] == "text/plain"
    assert document["status"] == "PENDING"
    assert "storage_key" not in document
    assert response.headers["location"] == f"{path}/{document['id']}"
    assert (
        tmp_path
        / "organizations"
        / organization["id"]
        / "documents"
        / document["id"]
        / "original.txt"
    ).read_bytes() == b"Knowledge base guide"
    assert queued_tasks == [
        ("outbox.publish_pending", None),
    ]

    async def read_outbox_message() -> OutboxMessage | None:
        async with concurrent_session_factory() as session:
            messages = list(
                await session.scalars(select(OutboxMessage)),
            )

        return next(
            (
                message
                for message in messages
                if message.payload == {"args": [document["id"]]}
            ),
            None,
        )

    outbox_message = asyncio.run(read_outbox_message())
    assert outbox_message is not None
    assert outbox_message.task_name == "documents.process_document"
    assert outbox_message.published_at is None


def test_upload_document_keeps_outbox_message_when_trigger_fails(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, headers = create_organization(client, "outbox-failure")
    configure_document_upload(monkeypatch, tmp_path)

    def send_task(*args, **kwargs) -> None:
        raise OperationalError("broker unavailable")

    monkeypatch.setattr(
        celery_app,
        "send_task",
        send_task,
    )

    response = client.post(
        f"/organizations/{organization['id']}/documents",
        headers=headers,
        files={
            "file": (
                "guide.txt",
                b"Knowledge base guide",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 201
    document = response.json()

    async def read_outbox_message() -> OutboxMessage | None:
        async with concurrent_session_factory() as session:
            messages = list(
                await session.scalars(select(OutboxMessage)),
            )

        return next(
            (
                message
                for message in messages
                if message.payload == {"args": [document["id"]]}
            ),
            None,
        )

    outbox_message = asyncio.run(read_outbox_message())
    assert outbox_message is not None
    assert outbox_message.published_at is None


def test_upload_document_rejects_unsupported_content_type(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    organization, headers = create_organization(client, "content-type")
    queued_tasks = configure_document_upload(monkeypatch, tmp_path)

    response = client.post(
        f"/organizations/{organization['id']}/documents",
        headers=headers,
        files={
            "file": (
                "guide.pdf",
                b"not a PDF yet",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 415
    assert response.json()["code"] == (
        "document_content_type_not_supported"
    )
    assert queued_tasks == []
    assert list(tmp_path.rglob("*")) == []


def test_upload_document_rejects_content_larger_than_limit(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    organization, headers = create_organization(client, "too-large")
    queued_tasks = configure_document_upload(monkeypatch, tmp_path)
    monkeypatch.setattr(
        settings,
        "document_upload_max_bytes",
        5,
    )

    response = client.post(
        f"/organizations/{organization['id']}/documents",
        headers=headers,
        files={
            "file": (
                "guide.txt",
                b"six-bytes",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 413
    assert response.json()["code"] == "document_too_large"
    assert queued_tasks == []
    assert list(tmp_path.rglob("*")) == []
