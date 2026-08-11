from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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