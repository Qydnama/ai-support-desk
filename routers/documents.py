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
from schemas.documents import (
    DocumentDownloadRead,
    DocumentRead,
    DocumentSearchCitationRead,
    DocumentSearchRead,
    DocumentSearchRequest,
)
from services import document_search
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


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    summary="Search organization documents",
)
async def search_organization_documents(
    request: DocumentSearchRequest,
    existing_organization: ExistingOrganizationDep,
    _permission: DocumentReadPermissionDep,
    session: SessionDep,
) -> DocumentSearchRead:
    result = await document_search.search_documents(
        session=session,
        organization_id=existing_organization.id,
        question=request.question,
        limit=request.limit,
    )

    return DocumentSearchRead(
        answer=result.answer,
        answer_not_found=result.answer_not_found,
        citations=[
            DocumentSearchCitationRead(
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
                chunk_index=citation.chunk_index,
                document_filename=citation.document_filename,
                page_start=citation.page_start,
                page_end=citation.page_end,
                score=citation.score,
            )
            for citation in result.citations
        ],
    )


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


@router.get(
    "/{document_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Create a temporary document download URL",
)
async def get_document_download_url(
    document: ExistingDocumentDep,
    _permission: DocumentReadPermissionDep,
) -> DocumentDownloadRead:
    download_url = (
        await document_service.create_document_download_url(document)
    )

    return DocumentDownloadRead(
        download_url=download_url,
    )


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
