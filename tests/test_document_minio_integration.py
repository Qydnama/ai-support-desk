import asyncio
import time
from datetime import timedelta
from hashlib import sha256
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from celery_app import celery_app
from core.enums import DocumentStatus
from models.documents import Document
from models.organizations import Organization
from models.users import User
from services import document_processing, documents as document_service
from services.document_storage import (
    create_document_storage_key,
    get_document_storage,
)
from settings import settings


class DisposableTestEngine:
    async def dispose(self) -> None:
        pass


def create_organization(
    client: TestClient,
    suffix: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    email = f"minio-document-{suffix}@example.com"
    password = "correct-horse-battery-staple"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"MinIO document user {suffix}",
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
            "name": f"MinIO document organization {suffix}",
            "slug": f"minio-documents-{suffix}",
        },
    )
    assert organization_response.status_code == 201

    return (
        organization_response.json(),
        headers,
        register_response.json(),
    )


def read_document(
    session_factory: async_sessionmaker[AsyncSession],
    document_id: UUID,
) -> Document | None:
    async def read() -> Document | None:
        async with session_factory() as session:
            return await session.get(Document, document_id)

    return asyncio.run(read())


def disable_outbox_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        celery_app,
        "send_task",
        lambda *args, **kwargs: None,
    )


def test_upload_and_worker_use_real_minio(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, headers, _ = create_organization(
        client,
        "upload-worker",
    )
    disable_outbox_trigger(monkeypatch)
    content = b"MinIO object read by the worker"
    response = client.post(
        f"/organizations/{organization['id']}/documents",
        headers=headers,
        files={"file": ("guide.txt", content, "text/plain")},
    )
    assert response.status_code == 201

    document_id = UUID(response.json()["id"])
    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    storage_key = document.storage_key
    storage = get_document_storage()

    try:
        assert document.organization_id == UUID(organization["id"])
        assert document.size_bytes == len(content)
        assert document.sha256 == sha256(content).hexdigest()
        assert storage.read_bytes(storage_key) == content

        monkeypatch.setattr(
            document_processing,
            "session_factory",
            concurrent_session_factory,
        )
        monkeypatch.setattr(
            document_processing,
            "engine",
            DisposableTestEngine(),
        )
        monkeypatch.setattr(
            document_processing,
            "embed_document_texts",
            lambda texts: [[0.1] for _ in texts],
        )
        monkeypatch.setattr(
            document_processing,
            "upsert_document_chunk_vectors",
            lambda **_: None,
        )
        asyncio.run(document_processing.process_document(document_id))

        processed_document = read_document(
            concurrent_session_factory,
            document_id,
        )
        assert processed_document is not None
        assert processed_document.status == DocumentStatus.COMPLETED
        assert processed_document.extracted_text == content.decode()
    finally:
        storage.delete(storage_key)


def test_failed_postgresql_commit_deletes_minio_object(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization_data, _, user_data = create_organization(
        client,
        "compensating-delete",
    )
    document_id = uuid4()
    organization_id = UUID(organization_data["id"])
    storage_key = create_document_storage_key(
        organization_id,
        document_id,
        content_type="text/plain",
    )
    storage = get_document_storage()
    monkeypatch.setattr(
        document_service,
        "uuid4",
        lambda: document_id,
    )

    async def create_with_failed_commit() -> None:
        async with concurrent_session_factory() as session:
            organization = await session.get(
                Organization,
                organization_id,
            )
            user = await session.get(User, UUID(user_data["id"]))
            assert organization is not None
            assert user is not None

            async def failed_commit() -> None:
                raise RuntimeError("forced PostgreSQL commit failure")

            monkeypatch.setattr(session, "commit", failed_commit)

            with pytest.raises(
                RuntimeError,
                match="forced PostgreSQL commit failure",
            ):
                await document_service.create_document(
                    session,
                    organization=organization,
                    uploaded_by_user=user,
                    original_filename="guide.txt",
                    content_type="text/plain",
                    content=b"Object that must be deleted",
                )

    asyncio.run(create_with_failed_commit())

    with pytest.raises(FileNotFoundError):
        storage.read_bytes(storage_key)


def test_download_url_is_private_tenant_scoped_and_expires(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, headers, _ = create_organization(
        client,
        "download-owner",
    )
    _, foreign_headers, _ = create_organization(
        client,
        "download-foreign",
    )
    disable_outbox_trigger(monkeypatch)
    content = b"Private MinIO document"
    documents_path = (
        f"/organizations/{organization['id']}/documents"
    )
    upload_response = client.post(
        documents_path,
        headers=headers,
        files={"file": ("private.txt", content, "text/plain")},
    )
    assert upload_response.status_code == 201

    document_id = UUID(upload_response.json()["id"])
    document = read_document(
        concurrent_session_factory,
        document_id,
    )
    assert document is not None
    storage = get_document_storage()

    try:
        download_response = client.get(
            f"{documents_path}/{document_id}/download",
            headers=headers,
        )
        assert download_response.status_code == 200
        download_url = download_response.json()["download_url"]

        foreign_response = client.get(
            f"{documents_path}/{document_id}/download",
            headers=foreign_headers,
        )
        assert foreign_response.status_code == 403

        public_object_url = (
            f"http://{settings.minio_public_endpoint}/"
            f"{settings.minio_documents_bucket}/"
            f"{quote(document.storage_key, safe='/')}"
        )
        with httpx.Client(trust_env=False) as http_client:
            assert http_client.get(public_object_url).status_code >= 400
            assert http_client.get(download_url).content == content

            expiring_url = storage.presigned_get_url(
                document.storage_key,
                expires=timedelta(seconds=1),
            )
            assert http_client.get(expiring_url).content == content
            time.sleep(2)
            assert http_client.get(expiring_url).status_code == 403
    finally:
        storage.delete(document.storage_key)
