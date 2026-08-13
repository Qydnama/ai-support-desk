from datetime import timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID

from minio import Minio
from minio.error import MinioException, S3Error
from urllib3.exceptions import HTTPError

from core.exceptions import DocumentStorageUnavailableError
from settings import settings


def create_document_storage_key(
    organization_id: UUID,
    document_id: UUID,
) -> str:
    return (
        f"organizations/{organization_id}/documents/"
        f"{document_id}/original.txt"
    )


def _validate_storage_key(
    storage_key: str,
) -> None:
    parts = storage_key.split("/")

    if (
        not storage_key
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError("storage key is invalid")


class DocumentStorage:
    """Локальная реализация, используемая только в unit-тестах."""

    def __init__(
        self,
        root: Path,
    ) -> None:
        self._root = root.resolve()

    def create_storage_key(
        self,
        document_id: UUID,
    ) -> str:
        return f"documents/{document_id}.txt"

    def write_bytes(
        self,
        storage_key: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        del content_type

        path = self._path_for(storage_key)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(content)

    def read_bytes(
        self,
        storage_key: str,
    ) -> bytes:
        return self._path_for(storage_key).read_bytes()

    def read_text(
        self,
        storage_key: str,
    ) -> str:
        return self.read_bytes(storage_key).decode("utf-8")

    def delete(
        self,
        storage_key: str,
    ) -> None:
        path = self._path_for(storage_key)

        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def _path_for(
        self,
        storage_key: str,
    ) -> Path:
        _validate_storage_key(storage_key)

        path = (self._root / storage_key).resolve()

        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise ValueError(
                "storage key must stay inside document storage",
            ) from exc

        if path == self._root:
            raise ValueError("storage key must identify a file")

        return path


class MinioDocumentStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        public_endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        public_secure: bool,
        bucket_name: str,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._public_client = Minio(
            public_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=public_secure,
        )

    def write_bytes(
        self,
        storage_key: str,
        content: bytes,
        *,
        content_type: str,
    ) -> None:
        _validate_storage_key(storage_key)

        try:
            self._client.put_object(
                bucket_name=self._bucket_name,
                object_name=storage_key,
                data=BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
        except S3Error as exc:
            raise DocumentStorageUnavailableError() from exc
        except (
            HTTPError,
            MinioException,
            OSError,
        ) as exc:
            raise DocumentStorageUnavailableError() from exc

    def read_bytes(
        self,
        storage_key: str,
    ) -> bytes:
        _validate_storage_key(storage_key)
        response = None

        try:
            response = self._client.get_object(
                bucket_name=self._bucket_name,
                object_name=storage_key,
            )
            return response.read()
        except S3Error as exc:
            if exc.code in {
                "NoSuchKey",
                "NoSuchObject",
                "NoSuchBucket",
            }:
                raise FileNotFoundError(
                    "document object does not exist",
                ) from exc

            raise DocumentStorageUnavailableError() from exc
        except (
            HTTPError,
            MinioException,
            OSError,
        ) as exc:
            raise DocumentStorageUnavailableError() from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def read_text(
        self,
        storage_key: str,
    ) -> str:
        return self.read_bytes(storage_key).decode("utf-8")

    def delete(
        self,
        storage_key: str,
    ) -> None:
        _validate_storage_key(storage_key)

        try:
            self._client.remove_object(
                bucket_name=self._bucket_name,
                object_name=storage_key,
            )
        except S3Error as exc:
            if exc.code in {
                "NoSuchKey",
                "NoSuchObject",
            }:
                return

            raise DocumentStorageUnavailableError() from exc
        except (
            HTTPError,
            MinioException,
            OSError,
        ) as exc:
            raise DocumentStorageUnavailableError() from exc

    def presigned_get_url(
        self,
        storage_key: str,
        *,
        expires: timedelta,
    ) -> str:
        _validate_storage_key(storage_key)

        try:
            return self._public_client.presigned_get_object(
                bucket_name=self._bucket_name,
                object_name=storage_key,
                expires=expires,
            )
        except S3Error as exc:
            raise DocumentStorageUnavailableError() from exc
        except (
            HTTPError,
            MinioException,
            OSError,
        ) as exc:
            raise DocumentStorageUnavailableError() from exc


def get_document_storage() -> MinioDocumentStorage:
    return MinioDocumentStorage(
        endpoint=settings.minio_endpoint,
        public_endpoint=settings.minio_public_endpoint,
        access_key=settings.minio_access_key.get_secret_value(),
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=settings.minio_secure,
        public_secure=settings.minio_public_secure,
        bucket_name=settings.minio_documents_bucket,
    )
