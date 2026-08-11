from pathlib import Path
from uuid import UUID

from settings import settings


class DocumentStorage:
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
    ) -> None:
        path = self._path_for(storage_key)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(content)

    def read_text(
        self,
        storage_key: str,
    ) -> str:
        return self._path_for(storage_key).read_text(
            encoding="utf-8",
        )

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
        if not storage_key:
            raise ValueError("storage key must not be empty")

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


def get_document_storage() -> DocumentStorage:
    return DocumentStorage(
        settings.document_storage_path,
    )