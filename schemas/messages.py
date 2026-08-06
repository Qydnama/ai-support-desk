from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.enums import MessageSenderType


class MessageCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    sender_type: MessageSenderType
    author_contact_id: UUID | None = None
    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    @model_validator(mode="after")
    def validate_author(self) -> MessageCreate:
        has_contact = self.author_contact_id is not None

        if self.sender_type is MessageSenderType.CONTACT:
            valid = has_contact
        else:
            valid = not has_contact

        if not valid:
            raise ValueError(
                "Author fields do not match sender_type",
            )

        return self


class MessageRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    conversation_id: UUID
    author_user_id: UUID | None
    author_contact_id: UUID | None
    sender_type: MessageSenderType
    content: str
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
