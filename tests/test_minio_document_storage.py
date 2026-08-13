from datetime import timedelta
from urllib.parse import urlparse
from uuid import uuid4

from services.document_storage import get_document_storage
from settings import settings


def test_minio_document_storage_writes_reads_deletes_and_presigns() -> None:
    storage = get_document_storage()
    storage_key = f"tests/{uuid4()}/document.txt"
    content = b"Knowledge base guide"

    try:
        storage.write_bytes(
            storage_key,
            content,
            content_type="text/plain",
        )

        assert storage.read_bytes(storage_key) == content
        assert storage.read_text(storage_key) == (
            "Knowledge base guide"
        )

        download_url = storage.presigned_get_url(
            storage_key,
            expires=timedelta(minutes=5),
        )

        assert (
            urlparse(download_url).netloc
            == settings.minio_public_endpoint
        )
        assert "X-Amz-Credential=" in download_url
        assert (
            settings.minio_secret_key.get_secret_value()
            not in download_url
        )
        assert (
            settings.minio_secret_key.get_secret_value()
            not in download_url
        )
    finally:
        storage.delete(storage_key)
