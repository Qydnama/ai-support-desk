from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import ConversationStatus


class ConversationCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    organization_id: UUID
    contact_id: UUID
    subject: str = Field(
        min_length=1,
        max_length=200,
    )


class ConversationUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: ConversationStatus
    expected_version: int = Field(ge=1)


class ConversationRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    organization_id: UUID
    contact_id: UUID
    assigned_user_id: UUID | None
    subject: str
    status: ConversationStatus
    version: int
    created_at: datetime
    updated_at: datetime


class ConversationFilters(BaseModel):
    organization_id: UUID
    status: ConversationStatus | None = None
