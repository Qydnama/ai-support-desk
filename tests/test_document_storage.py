from pathlib import Path
from uuid import uuid4

import pytest

from services.document_storage import DocumentStorage


def test_document_storage_writes_reads_and_deletes_file(
    tmp_path: Path,
) -> None:
    storage = DocumentStorage(tmp_path)
    document_id = uuid4()
    storage_key = storage.create_storage_key(document_id)

    storage.write_bytes(
        storage_key,
        b"Refunds are available within 30 days.",
    )

    assert storage_key == f"documents/{document_id}.txt"
    assert storage.read_text(storage_key) == (
        "Refunds are available within 30 days."
    )

    storage.delete(storage_key)
    storage.delete(storage_key)

    assert not (tmp_path / storage_key).exists()


@pytest.mark.parametrize(
    "storage_key",
    [
        "",
        "../outside.txt",
        "documents/../../outside.txt",
    ],
)
def test_document_storage_rejects_unsafe_storage_key(
    tmp_path: Path,
    storage_key: str,
) -> None:
    storage = DocumentStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.write_bytes(storage_key, b"unsafe")
