from typing import Annotated
from uuid import UUID

from fastapi import Depends

from core.exceptions import DocumentNotFoundError
from dependencies.database import SessionDep
from models.documents import Document
from repositories import documents as document_repository


async def get_existing_document(
    organization_id: UUID,
    document_id: UUID,
    session: SessionDep,
) -> Document:
    document = await document_repository.get_by_id(
        session=session,
        document_id=document_id,
        organization_id=organization_id,
    )

    if document is None:
        raise DocumentNotFoundError()

    return document


ExistingDocumentDep = Annotated[
    Document,
    Depends(get_existing_document),
]