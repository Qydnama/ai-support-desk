from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID
    original_filename: str
    content_type: str
    status: DocumentStatus
    extracted_text: str | None
    error_message: str | None
    processing_started_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentDownloadRead(BaseModel):
    download_url: str


class DocumentSearchRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1_000,
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class DocumentSearchCitationRead(BaseModel):
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    document_filename: str
    page_start: int | None
    page_end: int | None
    score: float


class DocumentSearchRead(BaseModel):
    answer: str | None
    answer_not_found: bool
    citations: list[DocumentSearchCitationRead]