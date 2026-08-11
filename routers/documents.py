import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, status
from kombu.exceptions import OperationalError

from celery_app import celery_app
from dependencies.auth import CurrentUserDep
from dependencies.database import SessionDep
from dependencies.documents import ExistingDocumentDep
from dependencies.organization_members import (
    DocumentCreatePermissionDep,
    DocumentReadPermissionDep,
)
from dependencies.organizations import ExistingOrganizationDep
from dependencies.pagination import PaginationDep
from repositories import documents as document_repository
from schemas.documents import DocumentRead
from services import documents as document_service
from settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/organizations/{organization_id}/documents",
    tags=["documents"],
)

DocumentUploadFile = Annotated[
    UploadFile,
    File(),
]


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List organization documents",
)
async def list_documents(
    existing_organization: ExistingOrganizationDep,
    _permission: DocumentReadPermissionDep,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[DocumentRead]:
    documents = await document_repository.list_by_organization(
        session=session,
        organization_id=existing_organization.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return [
        DocumentRead.model_validate(document)
        for document in documents
    ]


@router.get(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Get an organization document",
)
async def get_document(
    document: ExistingDocumentDep,
    _permission: DocumentReadPermissionDep,
) -> DocumentRead:
    return DocumentRead.model_validate(document)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Upload an organization document",
)
async def upload_document(
    file: DocumentUploadFile,
    existing_organization: ExistingOrganizationDep,
    current_user: CurrentUserDep,
    _permission: DocumentCreatePermissionDep,
    response: Response,
    session: SessionDep,
) -> DocumentRead:
    try:
        content = await file.read(
            settings.document_upload_max_bytes + 1,
        )
    finally:
        await file.close()

    document = await document_service.create_document(
        session=session,
        organization=existing_organization,
        uploaded_by_user=current_user,
        original_filename=file.filename,
        content_type=file.content_type,
        content=content,
    )

    try:
        await asyncio.to_thread(
            celery_app.send_task,
            "outbox.publish_pending",
        )
    except OperationalError:
        logger.warning(
            "outbox_publisher_trigger_failed "
            "document_id=%s organization_id=%s",
            document.id,
            existing_organization.id,
        )

    response.headers["Location"] = (
        f"/organizations/{existing_organization.id}"
        f"/documents/{document.id}"
    )

    return DocumentRead.model_validate(document)
