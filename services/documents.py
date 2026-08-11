import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    DocumentEncodingInvalidError,
    DocumentFilenameRequiredError,
    DocumentTooLargeError,
    UnsupportedDocumentContentTypeError,
)
from models.documents import Document
from models.organizations import Organization
from models.outbox_messages import OutboxMessage
from models.users import User
from services.document_storage import get_document_storage
from settings import settings

SUPPORTED_DOCUMENT_CONTENT_TYPE = "text/plain"
DOCUMENT_PROCESSING_TASK_NAME = "documents.process_document"


async def create_document(
    session: AsyncSession,
    *,
    organization: Organization,
    uploaded_by_user: User,
    original_filename: str | None,
    content_type: str | None,
    content: bytes,
) -> Document:
    normalized_filename = (
        (original_filename or "")
        .replace("\\", "/")
        .rsplit("/", maxsplit=1)[-1]
        .strip()
    )
    normalized_content_type = (
        (content_type or "")
        .split(";", maxsplit=1)[0]
        .strip()
        .lower()
    )

    if not normalized_filename:
        raise DocumentFilenameRequiredError()

    if len(normalized_filename) > 255:
        raise DocumentFilenameRequiredError()

    if normalized_content_type != SUPPORTED_DOCUMENT_CONTENT_TYPE:
        raise UnsupportedDocumentContentTypeError()

    if len(content) > settings.document_upload_max_bytes:
        raise DocumentTooLargeError()

    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentEncodingInvalidError() from exc

    document_id = uuid4()
    storage = get_document_storage()
    storage_key = storage.create_storage_key(document_id)

    document = Document(
        id=document_id,
        organization_id=organization.id,
        uploaded_by_user_id=uploaded_by_user.id,
        original_filename=normalized_filename,
        content_type=normalized_content_type,
        storage_key=storage_key,
    )

    try:
        await asyncio.to_thread(
            storage.write_bytes,
            storage_key,
            content,
        )
        session.add_all(
            [
                document,
                OutboxMessage(
                    task_name=DOCUMENT_PROCESSING_TASK_NAME,
                    payload={"args": [str(document.id)]},
                ),
            ],
        )
        await session.commit()
    except Exception:
        await session.rollback()

        try:
            await asyncio.to_thread(
                storage.delete,
                storage_key,
            )
        except Exception:
            pass

        raise

    return document
