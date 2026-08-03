from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    status: ConversationStatus | None = None
    assigned_user_id: UUID | None = None

    @field_validator("status")
    @classmethod
    def reject_null_status(
        cls,
        value: ConversationStatus | None,
    ) -> ConversationStatus:
        if value is None:
            raise ValueError("Field cannot be null; omit it instead")

        return value


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
    created_at: datetime
    updated_at: datetime


class ConversationFilters(BaseModel):
    organization_id: UUID
    status: ConversationStatus | None = None
